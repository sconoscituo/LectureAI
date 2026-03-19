from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """사용자 모델"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # 로그인 정보
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # 프리미엄 여부
    is_premium = Column(Boolean, default=False, nullable=False)

    # 이번 달 사용 횟수 (무료 플랜 제한용)
    monthly_usage = Column(Integer, default=0, nullable=False)

    # 사용량 초기화 기준 월 (YYYY-MM 형태로 저장)
    usage_reset_month = Column(String(7), default="", nullable=False)

    # 활성 계정 여부
    is_active = Column(Boolean, default=True, nullable=False)

    # 가입 및 수정 시각
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 강의 목록 (역참조)
    lectures = relationship("Lecture", back_populates="user", cascade="all, delete-orphan")
