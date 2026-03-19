import os
import json
import uuid
import aiofiles
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.lecture import Lecture
from app.schemas.lecture import LectureResponse, LectureListItem
from app.services.transcriber import transcribe_audio
from app.services.analyzer import analyze_lecture
from app.utils.auth import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/lectures", tags=["lectures"])
settings = get_settings()

# 허용 오디오 형식
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def _check_free_limit(user: User) -> None:
    """
    무료 사용자의 월 사용 횟수 초과 여부 확인.
    초과 시 HTTP 403 예외 발생.
    """
    if user.is_premium:
        return  # 프리미엄은 제한 없음

    # 월이 바뀌었으면 사용량 초기화
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    if user.usage_reset_month != current_month:
        user.monthly_usage = 0
        user.usage_reset_month = current_month

    if user.monthly_usage >= settings.max_free_uses_per_month:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"무료 플랜은 월 {settings.max_free_uses_per_month}회까지 사용 가능합니다. "
                "프리미엄으로 업그레이드하세요."
            ),
        )


def _check_duration_limit(user: User, duration: float) -> None:
    """무료 사용자의 음성 길이 초과 여부 확인."""
    if user.is_premium:
        return
    if duration > settings.max_free_duration_seconds:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"무료 플랜은 {settings.max_free_duration_seconds // 60}분 이하 파일만 분석 가능합니다. "
                "프리미엄으로 업그레이드하세요."
            ),
        )


def _build_response(lecture: Lecture) -> LectureResponse:
    """Lecture ORM 객체를 응답 스키마로 변환 (JSON 필드 파싱 포함)"""
    try:
        keywords = json.loads(lecture.keywords_json or "[]")
    except (json.JSONDecodeError, TypeError):
        keywords = []

    try:
        quiz_raw = json.loads(lecture.quiz_json or "[]")
    except (json.JSONDecodeError, TypeError):
        quiz_raw = []

    try:
        mindmap = json.loads(lecture.mindmap_json or "{}")
    except (json.JSONDecodeError, TypeError):
        mindmap = None

    return LectureResponse(
        id=lecture.id,
        filename=lecture.filename,
        duration_seconds=lecture.duration_seconds,
        transcript=lecture.transcript,
        summary=lecture.summary,
        keywords=keywords,
        quiz=quiz_raw,
        mindmap=mindmap,
        status=lecture.status,
        error_message=lecture.error_message or None,
        created_at=lecture.created_at,
    )


@router.post("/upload", response_model=LectureResponse, status_code=status.HTTP_201_CREATED)
async def upload_lecture(
    file: UploadFile = File(..., description="분석할 음성 파일 (mp3/wav/m4a)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    강의/녹음 파일 업로드 및 AI 분석

    1. 파일 형식 검사
    2. 무료 플랜 사용 횟수 확인
    3. 임시 파일 저장
    4. Whisper로 텍스트 변환
    5. 음성 길이 제한 확인
    6. Gemini로 요약/키워드/퀴즈/마인드맵 생성
    7. DB 저장 후 임시 파일 삭제
    """
    # 파일 확장자 확인
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 무료 플랜 횟수 체크 (파일 저장 전에 확인)
    _check_free_limit(current_user)

    # 임시 파일 경로 생성
    temp_filename = f"{uuid.uuid4()}{suffix}"
    temp_path = UPLOAD_DIR / temp_filename

    # DB에 처리 중 상태로 미리 기록
    lecture = Lecture(
        user_id=current_user.id,
        filename=file.filename,
        status="processing",
    )
    db.add(lecture)
    await db.flush()
    await db.refresh(lecture)

    try:
        # 파일을 임시 경로에 저장
        async with aiofiles.open(temp_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        # Whisper 음성 변환
        transcribe_result = await transcribe_audio(str(temp_path))
        transcript = transcribe_result["text"]
        duration = transcribe_result["duration"]

        # 무료 플랜 길이 제한 확인
        _check_duration_limit(current_user, duration)

        # Gemini 분석
        analysis = await analyze_lecture(transcript)

        # 분석 결과 DB 저장
        lecture.transcript = transcript
        lecture.duration_seconds = duration
        lecture.summary = analysis.get("summary", "")
        lecture.keywords_json = json.dumps(analysis.get("keywords", []), ensure_ascii=False)
        lecture.quiz_json = json.dumps(analysis.get("quiz", []), ensure_ascii=False)
        lecture.mindmap_json = json.dumps(analysis.get("mindmap", {}), ensure_ascii=False)
        lecture.status = "done"

        # 무료 사용 횟수 증가
        if not current_user.is_premium:
            current_month = datetime.now(timezone.utc).strftime("%Y-%m")
            current_user.usage_reset_month = current_month
            current_user.monthly_usage += 1

        await db.flush()

    except HTTPException:
        # 플랜 제한 예외는 그대로 재발생
        lecture.status = "error"
        lecture.error_message = "플랜 제한 초과"
        await db.flush()
        raise
    except Exception as e:
        lecture.status = "error"
        lecture.error_message = str(e)
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분석 중 오류가 발생했습니다: {str(e)}",
        )
    finally:
        # 임시 파일 반드시 삭제
        if temp_path.exists():
            os.remove(temp_path)

    return _build_response(lecture)


@router.get("", response_model=list[LectureListItem])
async def list_lectures(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내 강의 목록 조회 (최신순)"""
    result = await db.execute(
        select(Lecture)
        .where(Lecture.user_id == current_user.id)
        .order_by(Lecture.created_at.desc())
    )
    lectures = result.scalars().all()
    return lectures


@router.get("/{lecture_id}", response_model=LectureResponse)
async def get_lecture(
    lecture_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """특정 강의 상세 조회"""
    result = await db.execute(
        select(Lecture).where(
            Lecture.id == lecture_id,
            Lecture.user_id == current_user.id,
        )
    )
    lecture = result.scalar_one_or_none()
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="강의를 찾을 수 없습니다.",
        )
    return _build_response(lecture)


@router.delete("/{lecture_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lecture(
    lecture_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """강의 삭제"""
    result = await db.execute(
        select(Lecture).where(
            Lecture.id == lecture_id,
            Lecture.user_id == current_user.id,
        )
    )
    lecture = result.scalar_one_or_none()
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="강의를 찾을 수 없습니다.",
        )
    await db.delete(lecture)
