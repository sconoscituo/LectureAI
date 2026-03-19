from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class QuizQuestion(BaseModel):
    """퀴즈 문제 스키마"""
    question: str = Field(..., description="퀴즈 질문")
    options: List[str] = Field(..., description="선택지 목록 (4개)")
    answer: str = Field(..., description="정답 선택지")


class MindmapNode(BaseModel):
    """마인드맵 노드 스키마 (재귀 구조)"""
    topic: str = Field(..., description="노드 주제")
    children: List["MindmapNode"] = Field(default=[], description="하위 노드 목록")


# 재귀 모델 업데이트
MindmapNode.model_rebuild()


class LectureUpload(BaseModel):
    """강의 업로드 요청 스키마 (파일은 multipart로 별도 처리)"""
    pass


class LectureResponse(BaseModel):
    """강의 분석 결과 응답 스키마"""
    id: int
    filename: str
    duration_seconds: float
    transcript: str
    summary: str
    keywords: List[str] = Field(default=[], description="핵심 키워드 목록")
    quiz: List[QuizQuestion] = Field(default=[], description="퀴즈 목록")
    mindmap: Optional[MindmapNode] = Field(default=None, description="마인드맵 구조")
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LectureListItem(BaseModel):
    """강의 목록 아이템 스키마"""
    id: int
    filename: str
    duration_seconds: float
    summary: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """회원가입 요청 스키마"""
    email: str = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=8, description="비밀번호 (8자 이상)")


class UserLogin(BaseModel):
    """로그인 요청 스키마"""
    email: str
    password: str


class UserResponse(BaseModel):
    """사용자 정보 응답 스키마"""
    id: int
    email: str
    is_premium: bool
    monthly_usage: int

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT 토큰 응답 스키마"""
    access_token: str
    token_type: str = "bearer"
