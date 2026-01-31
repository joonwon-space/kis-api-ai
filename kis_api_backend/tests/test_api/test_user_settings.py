"""사용자 설정 API 엔드포인트 테스트"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.database import get_session
from app.db.models import User
from app.core.security import get_password_hash, create_access_token


@pytest.fixture(name="session")
def session_fixture():
    """테스트용 DB 세션"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """테스트용 FastAPI 클라이언트"""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """테스트용 사용자 생성"""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("password123"),
        full_name="Test User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="auth_token")
def auth_token_fixture(test_user: User):
    """테스트용 JWT 토큰"""
    token = create_access_token(data={"user_id": test_user.id, "email": test_user.email})
    return token


class TestUserSettingsAPI:
    """사용자 설정 API 통합 테스트"""

    def test_register_user_keys(
        self, client: TestClient, auth_token: str, session: Session
    ):
        """API 키 등록 엔드포인트 테스트"""
        response = client.post(
            "/api/v1/user/settings",
            json={
                "app_key": "TEST_APP_KEY_1234",
                "app_secret": "TEST_SECRET_5678",
                "account_no": "12345678",
                "acnt_prdt_cd": "01",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 201
        data = response.json()

        # 마스킹 처리 확인
        assert data["app_key_masked"] == "****1234"
        assert data["app_secret_masked"] == "****5678"
        assert data["account_no_masked"] == "****5678"
        assert data["acnt_prdt_cd"] == "01"
        assert "created_at" in data
        assert data["updated_at"] is None  # 최초 생성 시 None

    def test_register_user_keys_without_auth(self, client: TestClient):
        """인증 없이 API 키 등록 시도 (401 에러)"""
        response = client.post(
            "/api/v1/user/settings",
            json={
                "app_key": "TEST_KEY",
                "app_secret": "TEST_SECRET",
                "account_no": "12345678",
                "acnt_prdt_cd": "01",
            },
        )

        assert response.status_code == 401

    def test_get_user_keys(
        self, client: TestClient, auth_token: str, session: Session
    ):
        """API 키 조회 엔드포인트 테스트"""
        # 먼저 등록
        client.post(
            "/api/v1/user/settings",
            json={
                "app_key": "MY_APP_KEY_ABCD",
                "app_secret": "MY_SECRET_EFGH",
                "account_no": "87654321",
                "acnt_prdt_cd": "01",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # 조회
        response = client.get(
            "/api/v1/user/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # 마스킹 확인
        assert data["app_key_masked"] == "****ABCD"
        assert data["app_secret_masked"] == "****EFGH"
        assert data["account_no_masked"] == "****4321"
        assert data["acnt_prdt_cd"] == "01"

    def test_get_user_keys_not_found(self, client: TestClient, auth_token: str):
        """등록되지 않은 키 조회 시 404 에러"""
        response = client.get(
            "/api/v1/user/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404
        assert "등록된 API 키가 없습니다" in response.json()["detail"]

    def test_update_user_keys(
        self, client: TestClient, auth_token: str, session: Session
    ):
        """API 키 업데이트 테스트"""
        # 최초 등록
        response1 = client.post(
            "/api/v1/user/settings",
            json={
                "app_key": "OLD_KEY_1111",
                "app_secret": "OLD_SECRET_2222",
                "account_no": "11111111",
                "acnt_prdt_cd": "01",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response1.status_code == 201

        # 업데이트
        response2 = client.post(
            "/api/v1/user/settings",
            json={
                "app_key": "NEW_KEY_3333",
                "app_secret": "NEW_SECRET_4444",
                "account_no": "22222222",
                "acnt_prdt_cd": "01",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response2.status_code == 201

        # 조회하여 업데이트 확인
        response3 = client.get(
            "/api/v1/user/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response3.json()
        assert data["app_key_masked"] == "****3333"
        assert data["app_secret_masked"] == "****4444"
        assert data["account_no_masked"] == "****2222"

        # updated_at이 설정되어야 함
        assert data["updated_at"] is not None

    def test_invalid_token(self, client: TestClient):
        """잘못된 JWT 토큰으로 요청"""
        response = client.get(
            "/api/v1/user/settings",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == 401
