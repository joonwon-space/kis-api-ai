from datetime import datetime
from typing import Optional
from google.cloud import firestore
from app.schemas.user_key import UserKeyCreate, UserKeyDecrypted
from app.core.encryption import encryption_service


class UserKeyService:
    """사용자 API 키 관리 서비스 (Firestore 기반)

    사용자별 증권사 API 키를 암호화하여 Firestore에 저장하고 관리하는 비즈니스 로직.

    Firestore 구조:
        users/{email}/settings/kis_credentials
    """

    def __init__(self, db: firestore.Client):
        self.db = db

    def _get_credentials_doc_ref(self, user_email: str):
        """
        사용자의 KIS credentials document 참조 반환

        Args:
            user_email: 사용자 이메일

        Returns:
            DocumentReference: users/{email}/settings/kis_credentials
        """
        return (
            self.db.collection("users")
            .document(user_email)
            .collection("settings")
            .document("kis_credentials")
        )

    def create_or_update_user_key(
        self, user_email: str, data: UserKeyCreate
    ) -> dict:
        """사용자 API 키 생성 또는 업데이트

        Args:
            user_email: 사용자 이메일
            data: 평문 API 키 정보

        Returns:
            저장된 키 정보 (암호화된 상태)
        """
        doc_ref = self._get_credentials_doc_ref(user_email)
        doc = doc_ref.get()

        # 암호화된 데이터 생성
        encrypted_data = {
            "app_key_encrypted": encryption_service.encrypt(data.app_key),
            "app_secret_encrypted": encryption_service.encrypt(data.app_secret),
            "account_no_encrypted": encryption_service.encrypt(data.account_no),
            "acnt_prdt_cd_encrypted": encryption_service.encrypt(data.acnt_prdt_cd),
            "updated_at": datetime.utcnow().isoformat(),
        }

        if doc.exists:
            # 업데이트
            doc_ref.update(encrypted_data)
        else:
            # 생성
            encrypted_data["created_at"] = datetime.utcnow().isoformat()
            doc_ref.set(encrypted_data)

        return encrypted_data

    def get_user_key(self, user_email: str) -> Optional[dict]:
        """사용자 API 키 조회 (암호화된 상태)

        Args:
            user_email: 사용자 이메일

        Returns:
            암호화된 키 정보 또는 None
        """
        doc_ref = self._get_credentials_doc_ref(user_email)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        return doc.to_dict()

    def get_decrypted_keys(self, user_email: str) -> Optional[UserKeyDecrypted]:
        """복호화된 API 키 반환 (KIS API 호출용)

        Args:
            user_email: 사용자 이메일

        Returns:
            복호화된 키 정보 또는 None
        """
        user_key = self.get_user_key(user_email)
        if not user_key:
            return None

        return UserKeyDecrypted(
            app_key=encryption_service.decrypt(user_key["app_key_encrypted"]),
            app_secret=encryption_service.decrypt(user_key["app_secret_encrypted"]),
            account_no=encryption_service.decrypt(user_key["account_no_encrypted"]),
            acnt_prdt_cd=encryption_service.decrypt(
                user_key["acnt_prdt_cd_encrypted"]
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
