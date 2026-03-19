"""
강의 퀴즈 생성 라우터
"""
import json
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.lecture import Lecture
from app.utils.auth import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/quiz", tags=["퀴즈 생성"])
settings = get_settings()


class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    answer: str
    explanation: str


class QuizResponse(BaseModel):
    lecture_id: int
    lecture_title: str
    questions: List[QuizQuestion]
    total: int


@router.get("/{lecture_id}", response_model=QuizResponse)
async def generate_quiz(
    lecture_id: int,
    count: int = 5,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """강의 내용 기반 퀴즈 생성 (4지선다)"""
    result = await db.execute(
        select(Lecture).where(
            Lecture.id == lecture_id,
            Lecture.user_id == current_user.id
        )
    )
    lecture = result.scalar_one_or_none()
    if not lecture:
        raise HTTPException(404, "강의를 찾을 수 없습니다")

    if not lecture.summary:
        raise HTTPException(400, "강의 분석이 완료되지 않았습니다")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""다음 강의 내용을 바탕으로 4지선다 퀴즈 {count}개를 생성해줘.

강의 제목: {lecture.title}
강의 내용 요약:
{lecture.summary}

JSON 형식으로 반환 (마크다운 없이 순수 JSON):
[
  {{
    "question": "질문",
    "options": ["선택1", "선택2", "선택3", "선택4"],
    "answer": "정답 선택지 텍스트",
    "explanation": "해설"
  }}
]"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text[text.find("["):text.rfind("]") + 1]
        questions_data = json.loads(text)
        questions = [QuizQuestion(**q) for q in questions_data[:count]]
    except Exception:
        raise HTTPException(500, "퀴즈 생성 중 오류가 발생했습니다")

    return QuizResponse(
        lecture_id=lecture_id,
        lecture_title=lecture.title,
        questions=questions,
        total=len(questions),
    )
