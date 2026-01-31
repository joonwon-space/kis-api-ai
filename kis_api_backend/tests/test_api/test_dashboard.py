"""대시보드 API 엔드포인트 테스트"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch
from app.main import app
from app.db.database import get_session
from app.db.models import User, UserKey
from app.core.security import get_password_hash, create_access_token
from app.core.encryption import encryption_service


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
        email="dashboard@example.com",
        password_hash=get_password_hash("password123"),
        full_name="Dashboard User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_user_with_keys")
def test_user_with_keys_fixture(session: Session, test_user: User):
    """API 키가 등록된 테스트 사용자"""
    user_key = UserKey(
        user_id=test_user.id,
        app_key_encrypted=encryption_service.encrypt("TEST_APP_KEY"),
        app_secret_encrypted=encryption_service.encrypt("TEST_APP_SECRET"),
        account_no_encrypted=encryption_service.encrypt("12345678"),
        acnt_prdt_cd_encrypted=encryption_service.encrypt("01")
    )
    session.add(user_key)
    session.commit()
    return test_user


@pytest.fixture(name="auth_token")
def auth_token_fixture(test_user: User):
    """테스트용 JWT 토큰"""
    token = create_access_token(data={"user_id": test_user.id, "email": test_user.email})
    return token


@pytest.fixture(name="mock_kis_response")
def mock_kis_response_fixture():
    """Mock KIS API 응답"""
    return {
        "output1": [
            {
                "pdno": "005930",
                "prdt_name": "삼성전자",
                "hldg_qty": "10",
                "pchs_avg_pric": "70000",
                "prpr": "75000",
                "evlu_amt": "750000",
                "evlu_pfls_amt": "50000",
                "evlu_pfls_rt": "7.14"
            }
        ],
        "output2": [
            {
                "tot_evlu_amt": "750000",
                "dnca_tot_amt": "200000",
                "evlu_pfls_smtl_amt": "50000"
            }
        ]
    }


class TestDashboardAPI:
    """대시보드 API 통합 테스트"""

    def test_dashboard_summary_without_auth(self, client: TestClient):
        """인증 없이 요약 조회 시 401 에러"""
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 401

    def test_dashboard_summary_without_api_key(self, client: TestClient, auth_token: str):
        """API 키 없이 요약 조회 시 400 에러"""
        response = client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 400
        assert "API 키가 등록되지 않았습니다" in response.json()["detail"]

    @patch("kis_client.KISClient.get_balance")
    def test_dashboard_summary_with_api_key(
        self,
        mock_get_balance,
        client: TestClient,
        test_user_with_keys: User,
        mock_kis_response
    ):
        """API 키 있을 때 요약 조회 성공"""
        # Mock KIS API 응답
        mock_get_balance.return_value = mock_kis_response

        # JWT 토큰 생성
        token = create_access_token(
            data={"user_id": test_user_with_keys.id, "email": test_user_with_keys.email}
        )

        response = client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # 응답 필드 확인
        assert "total_assets" in data
        assert "total_deposit" in data
        assert "total_profit_loss" in data
        assert "stock_count" in data
        assert "profit_loss_rate" in data

        # 값 검증
        assert data["total_assets"] == "750000"
        assert data["total_deposit"] == "200000"
        assert data["total_profit_loss"] == "50000"
        assert data["stock_count"] == 1

    def test_dashboard_holdings_without_auth(self, client: TestClient):
        """인증 없이 보유 종목 조회 시 401 에러"""
        response = client.get("/api/v1/dashboard/holdings")
        assert response.status_code == 401

    def test_dashboard_holdings_without_api_key(self, client: TestClient, auth_token: str):
        """API 키 없이 보유 종목 조회 시 400 에러"""
        response = client.get(
            "/api/v1/dashboard/holdings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 400
        assert "API 키가 등록되지 않았습니다" in response.json()["detail"]

    @patch("kis_client.KISClient.get_balance")
    def test_dashboard_holdings_with_api_key(
        self,
        mock_get_balance,
        client: TestClient,
        test_user_with_keys: User,
        mock_kis_response
    ):
        """API 키 있을 때 보유 종목 조회 성공"""
        # Mock KIS API 응답
        mock_get_balance.return_value = mock_kis_response

        # JWT 토큰 생성
        token = create_access_token(
            data={"user_id": test_user_with_keys.id, "email": test_user_with_keys.email}
        )

        response = client.get(
            "/api/v1/dashboard/holdings",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # 응답 구조 확인
        assert "summary" in data
        assert "holdings" in data

        # 요약 정보 확인
        summary = data["summary"]
        assert summary["total_assets"] == "750000"
        assert summary["stock_count"] == 1

        # 보유 종목 확인
        holdings = data["holdings"]
        assert len(holdings) == 1
        assert holdings[0]["symbol"] == "005930"
        assert holdings[0]["name"] == "삼성전자"
        assert holdings[0]["quantity"] == "10"
        assert holdings[0]["market"] == "DOMESTIC"

    @patch("kis_client.KISClient.get_balance")
    def test_dashboard_holdings_empty(
        self,
        mock_get_balance,
        client: TestClient,
        test_user_with_keys: User
    ):
        """보유 종목이 없을 때"""
        # Mock: 보유 종목 없음
        mock_get_balance.return_value = {
            "output1": [],
            "output2": [
                {
                    "tot_evlu_amt": "0",
                    "dnca_tot_amt": "1000000",
                    "evlu_pfls_smtl_amt": "0"
                }
            ]
        }

        token = create_access_token(
            data={"user_id": test_user_with_keys.id, "email": test_user_with_keys.email}
        )

        response = client.get(
            "/api/v1/dashboard/holdings",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["stock_count"] == 0
        assert len(data["holdings"]) == 0
