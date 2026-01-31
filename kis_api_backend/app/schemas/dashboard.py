from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.holdings import HoldingItem


class DashboardSummary(BaseModel):
    """대시보드 요약 정보"""
    total_assets: str = Field(..., description="총 자산 평가액")
    total_deposit: str = Field(..., description="예수금 (현금)")
    total_profit_loss: str = Field(..., description="총 손익")
    profit_loss_rate: Optional[str] = Field(None, description="수익률 (%)")
    stock_count: int = Field(..., description="보유 종목 수")

    class Config:
        from_attributes = True


class DashboardHoldingsResponse(BaseModel):
    """대시보드 보유 종목 응답"""
    summary: DashboardSummary
    holdings: List[HoldingItem]

    class Config:
        from_attributes = True
