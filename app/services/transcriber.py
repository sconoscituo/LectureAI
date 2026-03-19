import whisper
import asyncio
from pathlib import Path
from app.config import get_settings

settings = get_settings()

# Whisper 모델을 전역에서 한 번만 로드 (서버 시작 시 초기화)
_model = None


def _get_model():
    """Whisper 모델 싱글턴 반환 (최초 호출 시 로드)"""
    global _model
    if _model is None:
        print(f"[Whisper] 모델 로딩 중: {settings.whisper_model_size}")
        _model = whisper.load_model(settings.whisper_model_size)
        print("[Whisper] 모델 로드 완료")
    return _model


def _transcribe_sync(audio_path: str) -> dict:
    """
    동기 방식으로 Whisper 음성 인식 수행
    - 반환값: {"text": str, "duration": float}
    """
    model = _get_model()

    # 한국어 우선 감지, 실패 시 자동 감지
    result = model.transcribe(
        audio_path,
        language=None,      # None = 자동 언어 감지
        verbose=False,
    )

    transcript = result.get("text", "").strip()

    # 전체 세그먼트에서 duration 계산
    segments = result.get("segments", [])
    duration = 0.0
    if segments:
        last_segment = segments[-1]
        duration = float(last_segment.get("end", 0.0))

    return {"text": transcript, "duration": duration}


async def transcribe_audio(audio_path: str) -> dict:
    """
    비동기 래퍼: 블로킹 Whisper 호출을 스레드풀에서 실행

    Args:
        audio_path: 음성 파일 경로 (mp3/wav/m4a 지원)

    Returns:
        {"text": 변환된 텍스트, "duration": 음성 길이(초)}

    Raises:
        FileNotFoundError: 파일이 없을 때
        RuntimeError: Whisper 처리 실패 시
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"음성 파일을 찾을 수 없습니다: {audio_path}")

    try:
        # CPU 블로킹 작업을 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _transcribe_sync, audio_path)
        return result
    except Exception as e:
        raise RuntimeError(f"Whisper 변환 실패: {str(e)}")
