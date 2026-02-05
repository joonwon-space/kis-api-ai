from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # KIS API Settings (기존 호환성 유지, 사용자별 키 사용 권장)
    app_key: Optional[str] = Field(default=None, alias="APP_KEY")
    app_secret: Optional[str] = Field(default=None, alias="APP_SECRET")
    account_no: Optional[str] = Field(default=None, alias="ACCOUNT_NO")
    acnt_prdt_cd: str = Field(default="01", alias="ACNT_PRDT_CD")
    is_simulation: bool = Field(default=True, alias="IS_SIMULATION")

    # JWT Authentication Settings
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        alias="SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Encryption Settings
    encryption_key: str = Field(..., alias="ENCRYPTION_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
try:
    settings = Settings()
    logger.info("Settings loaded successfully")
    logger.info(f"ENCRYPTION_KEY is {'set' if settings.encryption_key else 'NOT set'}")
except Exception as e:
    logger.error(f"Failed to load settings: {e}", exc_info=True)
    raise RuntimeError(f"설정 로딩 실패: ENCRYPTION_KEY 환경 변수를 확인해주세요. {str(e)}") from e
