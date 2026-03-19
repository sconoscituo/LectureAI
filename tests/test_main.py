import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    """테스트용 비동기 HTTP 클라이언트"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_root(client):
    """루트 엔드포인트 응답 확인"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "LectureAI"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health(client):
    """헬스 체크 엔드포인트 확인"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login(client):
    """회원가입 후 로그인 토큰 수령 확인"""
    # 회원가입
    reg_resp = await client.post(
        "/users/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert reg_resp.status_code == 201
    user = reg_resp.json()
    assert user["email"] == "test@example.com"
    assert user["is_premium"] is False

    # 로그인
    login_resp = await client.post(
        "/users/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """잘못된 비밀번호 로그인 거부 확인"""
    # 먼저 사용자 생성
    await client.post(
        "/users/register",
        json={"email": "wrong@example.com", "password": "correctpass"},
    )
    # 틀린 비밀번호로 로그인
    resp = await client.post(
        "/users/login",
        json={"email": "wrong@example.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_lectures_unauthorized(client):
    """인증 없이 강의 목록 접근 시 401 반환 확인"""
    resp = await client.get("/lectures")
    assert resp.status_code == 403  # HTTPBearer는 403 반환
