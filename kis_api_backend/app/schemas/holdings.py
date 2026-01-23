"""보유 종목 관련 스키마"""
from pydantic import BaseModel, Field
from typing import List, Optional
from .common import MarketType, Currency


class HoldingItem(BaseModel):
    """개별 보유 종목"""
    market: str = Field(..., description="시장 구분 (DOMESTIC/OVERSEAS)")
    symbol: str = Field(..., description="종목코드")
    name: str = Field(..., description="종목명")
    quantity: str = Field(..., description="보유수량")
    avg_price: str = Field(..., description="매입평균가")
    current_price: str = Field(..., description="현재가")
    evaluation_amount: str = Field(..., description="평가금액")
    profit_loss: str = Field(..., description="손익금액")
    profit_loss_rate: str = Field(..., description="수익률(%)")
    currency: Currency = Field(..., description="통화")


class HoldingsSummary(BaseModel):
    """보유 종목 요약"""
    total_evaluation: Optional[str] = Field(None, description="총 평가금액")
    total_purchase: Optional[str] = Field(None, description="총 매입금액")
    total_profit_loss: Optional[str] = Field(None, description="총 손익")
    profit_loss_rate: Optional[str] = Field(None, description="총 수익률(%)")


class HoldingsResponse(BaseModel):
    """보유 종목 조회 응답"""
    market_type: MarketType
    summary: HoldingsSummary
    holdings: List[HoldingItem]
