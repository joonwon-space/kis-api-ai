"""수익률 통계 스키마"""
from datetime import date
from typing import List
from pydantic import BaseModel, Field


class DailyAssetResponse(BaseModel):
    """일별 자산 응답"""
    date: date
    total_asset: float
    total_profit_loss: float
    profit_loss_rate: float
    deposit: float
    stock_evaluation: float

    class Config:
        from_attributes = True


class MonthlyStatResponse(BaseModel):
    """월별 통계 응답"""
    year_month: str  # "YYYY-MM" 형식
    start_asset: float  # 월초 자산
    end_asset: float  # 월말 자산
    profit_loss: float  # 월간 손익
    profit_loss_rate: float  # 월간 수익률 (%)
    avg_daily_asset: float  # 월평균 자산


class YearlyStatResponse(BaseModel):
    """연도별 통계 응답"""
    year: int
    start_asset: float  # 연초 자산
    end_asset: float  # 연말 자산
    profit_loss: float  # 연간 손익
    profit_loss_rate: float  # 연간 수익률 (%)
    max_asset: float  # 최고 자산
    min_asset: float  # 최저 자산
    avg_monthly_return: float  # 월평균 수익률 (%)


class DailyStatsListResponse(BaseModel):
    """일별 통계 리스트 응답"""
    success: bool = True
    data: List[DailyAssetResponse]
    total: int = Field(description="총 데이터 개수")


class MonthlyStatsListResponse(BaseModel):
    """월별 통계 리스트 응답"""
    success: bool = True
    data: List[MonthlyStatResponse]
    total: int = Field(description="총 데이터 개수")


class YearlyStatsListResponse(BaseModel):
    """연도별 통계 리스트 응답"""
    success: bool = True
    data: List[YearlyStatResponse]
    total: int = Field(description="총 데이터 개수")
