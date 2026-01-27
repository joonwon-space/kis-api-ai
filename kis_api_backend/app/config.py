from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # KIS API Settings
    app_key: str = Field(..., alias="APP_KEY")
    app_secret: str = Field(..., alias="APP_SECRET")
    account_no: str = Field(..., alias="ACCOUNT_NO")
    acnt_prdt_cd: str = Field(..., alias="ACNT_PRDT_CD")
    is_simulation: bool = Field(default=True, alias="IS_SIMULATION")

    # JWT Authentication Settings
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        alias="SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
