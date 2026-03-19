from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Lecture(Base):
    """강의/녹음 분석 결과 모델"""

    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True)

    # 소유 사용자
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 원본 파일 정보
    filename = Column(String(255), nullable=False)

    # 음성 길이 (초 단위)
    duration_seconds = Column(Float, default=0.0)

    # Whisper 변환 결과 텍스트
    transcript = Column(Text, default="")

    # Gemini 분석 결과 (각각 JSON 문자열로 저장)
    summary = Column(Text, default="")           # 핵심 요약 텍스트
    keywords_json = Column(Text, default="[]")   # 키워드 배열 JSON
    quiz_json = Column(Text, default="[]")        # 퀴즈 배열 JSON
    mindmap_json = Column(Text, default="{}")     # 마인드맵 JSON

    # 처리 상태 (pending / processing / done / error)
    status = Column(String(20), default="pending", nullable=False)

    # 오류 메시지 (status=error일 때)
    error_message = Column(Text, default="")

    # 생성 시각
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 사용자 역참조
    user = relationship("User", back_populates="lectures")
