# LectureAI - 설정 및 사용 가이드

## 프로젝트 소개

강의 및 녹음 파일을 업로드하면 Whisper로 음성을 텍스트로 변환하고, Gemini AI로 요약·퀴즈·마인드맵을 자동 생성하는 서비스입니다.

---

## 필요한 API 키 / 환경변수 목록

| 변수명 | 설명 | 발급 URL |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini AI API 키 | https://aistudio.google.com/app/apikey |
| `SECRET_KEY` | JWT 서명용 비밀 키 (임의의 긴 문자열) | 직접 생성 (예: `openssl rand -hex 32`) |
| `DATABASE_URL` | 데이터베이스 연결 URL (기본: SQLite) | - |
| `WHISPER_MODEL_SIZE` | Whisper 모델 크기 (`tiny` / `base` / `small` / `medium` / `large`) | - |
| `MAX_FREE_USES_PER_MONTH` | 무료 플랜 월 사용 횟수 제한 (기본: 3) | - |
| `MAX_FREE_DURATION_SECONDS` | 무료 플랜 최대 음성 길이 초 (기본: 600 = 10분) | - |

---

## GitHub Secrets 설정 방법

저장소 페이지 > **Settings** > **Secrets and variables** > **Actions** > **New repository secret**

| Secret 이름 | 값 |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio에서 발급한 키 |
| `SECRET_KEY` | 프로덕션용 JWT 비밀 키 |

---

## 로컬 개발 환경 설정

### 1. `.env` 파일 생성

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite+aiosqlite:///./lectureai.db
WHISPER_MODEL_SIZE=base
DEBUG=true
MAX_FREE_USES_PER_MONTH=3
MAX_FREE_DURATION_SECONDS=600
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

> Whisper 사용을 위해 ffmpeg가 시스템에 설치되어 있어야 합니다.
> - macOS: `brew install ffmpeg`
> - Ubuntu: `sudo apt install ffmpeg`
> - Windows: https://ffmpeg.org/download.html

---

## 실행 방법

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI를 확인할 수 있습니다.

### Docker로 실행

```bash
docker-compose up --build
```

---

## API 엔드포인트 주요 사용법

### 헬스 체크

```
GET /health
```

### 회원가입

```
POST /users/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

### 로그인 (JWT 토큰 발급)

```
POST /users/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

응답으로 받은 `access_token`을 이후 요청의 `Authorization: Bearer <token>` 헤더에 포함합니다.

### 강의 파일 업로드 및 분석

```
POST /lectures/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <음성 파일 (.mp3 / .wav / .m4a / .ogg / .flac)>
```

응답에 `transcript`(전사 텍스트), `summary`(요약), `keywords`(키워드), `quiz`(퀴즈), `mindmap`(마인드맵) 포함.

### 강의 목록 조회

```
GET /lectures/
Authorization: Bearer <access_token>
```

### 강의 상세 조회

```
GET /lectures/{lecture_id}
Authorization: Bearer <access_token>
```

---

전체 API 문서: http://localhost:8000/docs
