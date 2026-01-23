"""주식 시세 관련 스키마"""
from pydantic import BaseModel, Field
from .common import Currency


class StockInfo(BaseModel):
    """종목 정보"""
    market: str = Field(..., description="시장 구분 (DOMESTIC/OVERSEAS)")
    symbol: str = Field(..., description="종목코드/심볼")
    name: str = Field(..., description="종목명")


class StockQuote(BaseModel):
    """주식 현재가 시세"""
    market: str = Field(..., description="시장 구분 (DOMESTIC/OVERSEAS)")
    symbol: str = Field(..., description="종목코드/심볼")
    name: str = Field(..., description="종목명")
    current_price: str = Field(..., description="현재가")
    change: str = Field(..., description="전일대비 (절대값)")
    change_rate: str = Field(..., description="등락률(%)")
    change_direction: str = Field(..., description="등락 방향 (UP/DOWN/UNCHANGED)")
    volume: str = Field(..., description="거래량")
    open: str = Field(..., description="시가")
    high: str = Field(..., description="고가")
    low: str = Field(..., description="저가")
    currency: Currency = Field(..., description="통화 (KRW/USD)")
    updated_at: str = Field(..., description="조회 시각 (ISO 8601)")
