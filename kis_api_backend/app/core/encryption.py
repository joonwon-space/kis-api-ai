from cryptography.fernet import Fernet
from app.config import settings


class EncryptionService:
    """Fernet 기반 암호화/복호화 서비스

    사용자별 증권사 API Key를 안전하게 DB에 저장하기 위한 암호화 유틸리티.
    대칭키 암호화(Fernet)를 사용하여 암호화/복호화 수행.
    """

    def __init__(self):
        """암호화 서비스 초기화

        환경변수 ENCRYPTION_KEY로부터 암호화 키를 로드.
        키는 Fernet.generate_key()로 생성된 32바이트 URL-safe base64 문자열이어야 함.
        """
        self.cipher = Fernet(settings.encryption_key.encode())

    def encrypt(self, plain_text: str) -> str:
        """평문을 암호화

        Args:
            plain_text: 암호화할 평문 문자열

        Returns:
            base64 인코딩된 암호문 문자열
        """
        if not plain_text:
            return ""
        return self.cipher.encrypt(plain_text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        """암호문을 복호화

        Args:
            encrypted_text: 복호화할 암호문 문자열

        Returns:
            복호화된 평문 문자열

        Raises:
            cryptography.fernet.InvalidToken: 잘못된 암호문이거나 키가 일치하지 않는 경우
        """
        if not encrypted_text:
            return ""
        return self.cipher.decrypt(encrypted_text.encode()).decode()


# 싱글톤 인스턴스
encryption_service = EncryptionService()
