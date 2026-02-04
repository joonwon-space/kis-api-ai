from datetime import datetime, date
from typing import Optional
from sqlmodel import Field, SQLModel, Index


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


class DailyAsset(SQLModel, table=True):
    """일별 자산 스냅샷

    사용자의 일별 자산 현황을 저장하여 수익률 추이를 추적합니다.
    """
    __tablename__ = "daily_assets"
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'snapshot_date', unique=True),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    snapshot_date: date = Field(index=True)

    # 자산 정보
    total_asset: float = Field(default=0.0)  # 총 자산 (평가금액 + 예수금)
    total_purchase_amount: float = Field(default=0.0)  # 총 매입금액
    total_profit_loss: float = Field(default=0.0)  # 총 평가손익 (평가금액 - 매입금액)
    profit_loss_rate: float = Field(default=0.0)  # 수익률 (%)

    # 세부 정보
    deposit: float = Field(default=0.0)  # 예수금
    stock_evaluation: float = Field(default=0.0)  # 주식 평가금액

    created_at: datetime = Field(default_factory=datetime.utcnow)
