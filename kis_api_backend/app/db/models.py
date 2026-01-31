from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """사용자 모델"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # 추후 확장 가능 필드
    full_name: Optional[str] = Field(default=None, max_length=100)
    auth_provider: str = Field(default="email", max_length=50)  # "email", "google", etc.


class UserKey(SQLModel, table=True):
    """사용자별 증권사 API 키 (암호화 저장)

    사용자마다 다른 증권사 계좌의 API Key를 안전하게 저장.
    모든 민감 정보는 Fernet 암호화 후 저장됨.
    """
    __tablename__ = "user_keys"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)

    # 암호화된 필드 (Fernet으로 암호화된 base64 문자열 저장)
    app_key_encrypted: str = Field(max_length=500)
    app_secret_encrypted: str = Field(max_length=500)
    account_no_encrypted: str = Field(max_length=500)
    acnt_prdt_cd_encrypted: str = Field(max_length=500)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
