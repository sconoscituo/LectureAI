# LectureAI

강의 및 녹음 파일을 업로드하면 AI가 자동으로 텍스트 변환 후 핵심 요약, 키워드, 퀴즈, 마인드맵을 생성해주는 서비스입니다.

## 주요 기능

- **음성 변환**: OpenAI Whisper를 사용한 mp3/wav/m4a 파일 텍스트 변환
- **AI 분석**: Google Gemini AI를 통한 핵심 요약, 키워드 추출
- **퀴즈 생성**: 강의 내용 기반 자동 퀴즈 생성
- **마인드맵**: 강의 구조를 시각화하는 마인드맵 데이터 생성
- **구독 모델**: 무료(월 3회, 10분 이하) / 프리미엄(무제한)

## 시작하기

### 환경 설정

```bash
cp .env.example .env
# .env 파일에서 API 키 설정
```

### 설치 및 실행

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Docker로 실행

```bash
docker-compose up -d
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /lectures/upload | 강의 파일 업로드 및 분석 |
| GET | /lectures | 내 강의 목록 조회 |
| GET | /lectures/{id} | 강의 상세 조회 |
| DELETE | /lectures/{id} | 강의 삭제 |
| POST | /users/register | 회원가입 |
| POST | /users/login | 로그인 |

## 기술 스택

- **Backend**: FastAPI, SQLAlchemy, aiosqlite
- **AI**: OpenAI Whisper (음성인식), Google Gemini (분석)
- **Auth**: JWT (python-jose)
- **배포**: Docker, docker-compose

## 수익 구조

- **무료**: 월 3회 분석, 10분 이하 음성 파일
- **프리미엄**: 무제한 분석, 무제한 길이, PDF 내보내기
