from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserKeyCreate(BaseModel):
    """사용자 API 키 등록 요청 (평문)"""
    app_key: str = Field(..., description="증권사 APP Key")
    app_secret: str = Field(..., description="증권사 APP Secret")
    account_no: str = Field(..., description="계좌번호")
    acnt_prdt_cd: str = Field(default="01", description="계좌상품코드 (01: 종합계좌)")


class UserKeyResponse(BaseModel):
    """사용자 API 키 조회 응답 (마스킹 처리)"""
    app_key_masked: str = Field(..., description="마스킹된 APP Key (예: ****1234)")
    app_secret_masked: str = Field(..., description="마스킹된 APP Secret")
    account_no_masked: str = Field(..., description="마스킹된 계좌번호")
    acnt_prdt_cd: str = Field(..., description="계좌상품코드")
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserKeyDecrypted(BaseModel):
    """복호화된 사용자 키 (내부 사용 전용)"""
    app_key: str
    app_secret: str
    account_no: str
    acnt_prdt_cd: str
