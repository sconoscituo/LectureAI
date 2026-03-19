from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import lectures, users
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 이벤트 처리"""
    # 시작 시 DB 테이블 생성
    await init_db()
    print("[LectureAI] 서버 시작 완료")
    yield
    print("[LectureAI] 서버 종료")


app = FastAPI(
    title="LectureAI",
    description="강의/녹음 분석 AI - Whisper 음성 변환 + Gemini 요약/퀴즈/마인드맵",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정 (개발 중 전체 허용, 프로덕션에서는 origins 지정 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(users.router)
app.include_router(lectures.router)


@app.get("/", tags=["health"])
async def root():
    """헬스 체크 엔드포인트"""
    return {
        "service": "LectureAI",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """서버 상태 확인"""
    return {"status": "ok"}
