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

    def to_dict(self) -> dict:
        """
        Firestore 저장용 딕셔너리 변환

        Note:
        - id 필드는 제외 (Firestore document ID로 email 사용)
        - datetime을 ISO 문자열로 변환
        """
        return {
            "email": self.email,
            "password_hash": self.password_hash,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "full_name": self.full_name,
            "auth_provider": self.auth_provider,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """
        Firestore 데이터를 User 모델로 변환

        Args:
            data: Firestore document 데이터

        Returns:
            User: User 모델 인스턴스
        """
        # ISO 문자열을 datetime 객체로 변환
        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(data["created_at"])
            else:
                created_at = data["created_at"]

        updated_at = None
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(data["updated_at"])
            else:
                updated_at = data["updated_at"]

        return cls(
            email=data["email"],
            password_hash=data["password_hash"],
            is_active=data.get("is_active", True),
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at,
            full_name=data.get("full_name"),
            auth_provider=data.get("auth_provider", "email"),
        )


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
