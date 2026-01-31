"""암호화 유틸리티 테스트"""

import pytest
from cryptography.fernet import Fernet
from app.core.encryption import EncryptionService


class TestEncryptionService:
    """EncryptionService 단위 테스트"""

    def test_encryption_decryption(self):
        """암호화/복호화 정상 동작 확인"""
        service = EncryptionService()
        plain = "test_app_key_1234"
        encrypted = service.encrypt(plain)

        # 암호화된 값은 평문과 달라야 함
        assert encrypted != plain
        # 복호화하면 원본과 일치해야 함
        assert service.decrypt(encrypted) == plain

    def test_encrypted_value_is_not_readable(self):
        """암호화된 값이 평문과 전혀 다름을 확인"""
        service = EncryptionService()
        plain = "my_secret_key"
        encrypted = service.encrypt(plain)

        # 평문이 암호문에 포함되지 않아야 함 (보안 검증)
        assert plain not in encrypted
        # Fernet 암호문은 gAAAA로 시작
        assert encrypted.startswith("gAAAA")

    def test_empty_string_encryption(self):
        """빈 문자열 암호화 처리"""
        service = EncryptionService()
        encrypted = service.encrypt("")

        assert encrypted == ""
        assert service.decrypt(encrypted) == ""

    def test_unicode_encryption(self):
        """유니코드 문자열 암호화"""
        service = EncryptionService()
        plain = "한글테스트_123"
        encrypted = service.encrypt(plain)

        assert service.decrypt(encrypted) == plain

    def test_long_text_encryption(self):
        """긴 텍스트 암호화"""
        service = EncryptionService()
        plain = "A" * 1000
        encrypted = service.encrypt(plain)

        assert service.decrypt(encrypted) == plain

    def test_different_instances_same_key(self):
        """서로 다른 인스턴스가 같은 키를 사용하는지 확인"""
        service1 = EncryptionService()
        service2 = EncryptionService()

        plain = "test_value"
        encrypted = service1.encrypt(plain)

        # 다른 인스턴스로 복호화 가능해야 함
        assert service2.decrypt(encrypted) == plain

    def test_invalid_decryption(self):
        """잘못된 암호문 복호화 시 예외 발생"""
        service = EncryptionService()

        with pytest.raises(Exception):  # InvalidToken 예외
            service.decrypt("invalid_encrypted_data")
