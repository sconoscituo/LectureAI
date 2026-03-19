from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정 - .env 파일에서 자동으로 값을 읽어옴"""

    # Gemini AI API 키
    gemini_api_key: str = "your_gemini_api_key"

    # 데이터베이스 URL (기본값: SQLite)
    database_url: str = "sqlite+aiosqlite:///./lectureai.db"

    # JWT 시크릿 키
    secret_key: str = "your_secret_key_change_in_production"

    # JWT 알고리즘
    algorithm: str = "HS256"

    # JWT 만료 시간 (분)
    access_token_expire_minutes: int = 60 * 24  # 24시간

    # 디버그 모드
    debug: bool = True

    # 무료 플랜 월 사용 횟수 제한
    max_free_uses_per_month: int = 3

    # 무료 플랜 최대 음성 길이 (초) - 기본 10분
    max_free_duration_seconds: int = 600

    # Whisper 모델 크기 (tiny, base, small, medium, large)
    whisper_model_size: str = "base"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글턴 반환 (캐시 적용)"""
    return Settings()
