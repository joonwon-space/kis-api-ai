from datetime import datetime
from typing import Optional
from sqlmodel import Session, select
from app.db.models import UserKey
from app.schemas.user_key import UserKeyCreate, UserKeyDecrypted
from app.core.encryption import encryption_service


class UserKeyService:
    """사용자 API 키 관리 서비스

    사용자별 증권사 API 키를 암호화하여 저장하고 관리하는 비즈니스 로직.
    """

    def __init__(self, session: Session):
        self.session = session

    def create_or_update_user_key(
        self, user_id: int, data: UserKeyCreate
    ) -> UserKey:
        """사용자 API 키 생성 또는 업데이트

        Args:
            user_id: 사용자 ID
            data: 평문 API 키 정보

        Returns:
            생성 또는 업데이트된 UserKey 인스턴스
        """
        # 기존 키 확인
        statement = select(UserKey).where(UserKey.user_id == user_id)
        user_key = self.session.exec(statement).first()

        if user_key:
            # 업데이트
            user_key.app_key_encrypted = encryption_service.encrypt(data.app_key)
            user_key.app_secret_encrypted = encryption_service.encrypt(
                data.app_secret
            )
            user_key.account_no_encrypted = encryption_service.encrypt(
                data.account_no
            )
            user_key.acnt_prdt_cd_encrypted = encryption_service.encrypt(
                data.acnt_prdt_cd
            )
            user_key.updated_at = datetime.utcnow()
        else:
            # 생성
            user_key = UserKey(
                user_id=user_id,
                app_key_encrypted=encryption_service.encrypt(data.app_key),
                app_secret_encrypted=encryption_service.encrypt(data.app_secret),
                account_no_encrypted=encryption_service.encrypt(data.account_no),
                acnt_prdt_cd_encrypted=encryption_service.encrypt(
                    data.acnt_prdt_cd
                ),
            )
            self.session.add(user_key)

        self.session.commit()
        self.session.refresh(user_key)
        return user_key

    def get_user_key(self, user_id: int) -> Optional[UserKey]:
        """사용자 API 키 조회 (암호화된 상태)

        Args:
            user_id: 사용자 ID

        Returns:
            UserKey 인스턴스 또는 None
        """
        statement = select(UserKey).where(UserKey.user_id == user_id)
        return self.session.exec(statement).first()

    def get_decrypted_keys(self, user_id: int) -> Optional[UserKeyDecrypted]:
        """복호화된 API 키 반환 (KIS API 호출용)

        Args:
            user_id: 사용자 ID

        Returns:
            복호화된 키 정보 또는 None
        """
        user_key = self.get_user_key(user_id)
        if not user_key:
            return None

        return UserKeyDecrypted(
            app_key=encryption_service.decrypt(user_key.app_key_encrypted),
            app_secret=encryption_service.decrypt(user_key.app_secret_encrypted),
            account_no=encryption_service.decrypt(user_key.account_no_encrypted),
            acnt_prdt_cd=encryption_service.decrypt(
                user_key.acnt_prdt_cd_encrypted
            ),
        )

    @staticmethod
    def mask_value(value: str) -> str:
        """마스킹 처리 (뒤 4자만 표시)

        Args:
            value: 마스킹할 문자열

        Returns:
            마스킹된 문자열 (예: ****1234)
        """
        if not value or len(value) <= 4:
            return "****"
        return f"****{value[-4:]}"
