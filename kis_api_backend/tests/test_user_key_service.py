"""사용자 키 서비스 테스트"""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from app.db.models import User, UserKey
from app.schemas.user_key import UserKeyCreate
from app.services.user_key_service import UserKeyService
from app.core.security import get_password_hash


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


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """테스트용 사용자"""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("password123"),
        full_name="Test User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestUserKeyService:
    """UserKeyService 단위 테스트"""

    def test_create_user_key(self, session: Session, test_user: User):
        """UserKey 생성 테스트"""
        service = UserKeyService(session)
        data = UserKeyCreate(
            app_key="TEST_APP_KEY_1234",
            app_secret="TEST_APP_SECRET_5678",
            account_no="12345678",
            acnt_prdt_cd="01",
        )

        user_key = service.create_or_update_user_key(test_user.id, data)

        # DB에 저장됨
        assert user_key.id is not None
        assert user_key.user_id == test_user.id

        # DB에는 암호문으로 저장됨 (평문이 아님)
        assert user_key.app_key_encrypted != data.app_key
        assert user_key.app_secret_encrypted != data.app_secret
        assert user_key.account_no_encrypted != data.account_no

        # Fernet 암호문 형식 확인
        assert user_key.app_key_encrypted.startswith("gAAAA")
        assert user_key.app_secret_encrypted.startswith("gAAAA")

    def test_get_decrypted_keys(self, session: Session, test_user: User):
        """복호화된 키 조회 테스트"""
        service = UserKeyService(session)
        data = UserKeyCreate(
            app_key="TEST_KEY",
            app_secret="TEST_SECRET",
            account_no="87654321",
            acnt_prdt_cd="01",
        )

        # 키 생성
        service.create_or_update_user_key(test_user.id, data)

        # 복호화하면 원본과 일치
        decrypted = service.get_decrypted_keys(test_user.id)
        assert decrypted is not None
        assert decrypted.app_key == data.app_key
        assert decrypted.app_secret == data.app_secret
        assert decrypted.account_no == data.account_no
        assert decrypted.acnt_prdt_cd == data.acnt_prdt_cd

    def test_update_user_key(self, session: Session, test_user: User):
        """UserKey 업데이트 테스트"""
        service = UserKeyService(session)

        # 최초 생성
        data1 = UserKeyCreate(
            app_key="OLD_KEY",
            app_secret="OLD_SECRET",
            account_no="11111111",
            acnt_prdt_cd="01",
        )
        user_key1 = service.create_or_update_user_key(test_user.id, data1)
        old_id = user_key1.id

        # 업데이트
        data2 = UserKeyCreate(
            app_key="NEW_KEY",
            app_secret="NEW_SECRET",
            account_no="22222222",
            acnt_prdt_cd="01",
        )
        user_key2 = service.create_or_update_user_key(test_user.id, data2)

        # 같은 레코드를 업데이트 (새로 생성 X)
        assert user_key2.id == old_id

        # 새 값으로 업데이트됨
        decrypted = service.get_decrypted_keys(test_user.id)
        assert decrypted.app_key == "NEW_KEY"
        assert decrypted.app_secret == "NEW_SECRET"
        assert decrypted.account_no == "22222222"

    def test_get_user_key_not_found(self, session: Session):
        """존재하지 않는 사용자 키 조회"""
        service = UserKeyService(session)
        user_key = service.get_user_key(user_id=9999)

        assert user_key is None

    def test_get_decrypted_keys_not_found(self, session: Session):
        """존재하지 않는 사용자 키 복호화 조회"""
        service = UserKeyService(session)
        decrypted = service.get_decrypted_keys(user_id=9999)

        assert decrypted is None

    def test_masking(self):
        """마스킹 로직 테스트"""
        # 정상 케이스 (8자 이상)
        masked = UserKeyService.mask_value("ABCDEFGH1234")
        assert masked == "****1234"

        # 짧은 문자열 (3자)
        masked_short = UserKeyService.mask_value("ABC")
        assert masked_short == "****"

        # 빈 문자열
        masked_empty = UserKeyService.mask_value("")
        assert masked_empty == "****"

        # 딱 4자
        masked_four = UserKeyService.mask_value("1234")
        assert masked_four == "****"

        # 5자 (뒤 4자 표시)
        masked_five = UserKeyService.mask_value("12345")
        assert masked_five == "****2345"
