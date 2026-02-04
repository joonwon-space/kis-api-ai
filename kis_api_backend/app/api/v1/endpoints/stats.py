"""통계 API 엔드포인트 (Firestore 기반)"""
from fastapi import APIRouter, Depends, Query
from google.cloud import firestore
from app.db.firestore import get_firestore_db
from app.core.deps import get_current_user
from app.db.models import User
from app.services.stats_service import StatsService
from app.schemas.stats import (
    DailyStatsListResponse,
    MonthlyStatsListResponse,
    YearlyStatsListResponse
)

router = APIRouter()


@router.get("/daily", response_model=DailyStatsListResponse)
def get_daily_stats(
    days: int = Query(default=30, ge=1, le=365, description="조회할 일수"),
    current_user: User = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore_db)
):
    """
    일별 자산 통계 조회

    최근 N일간의 일별 자산 변동 추이를 Firestore에서 조회합니다.

    Args:
        days: 조회할 일수 (1~365, 기본값: 30)

    Returns:
        DailyStatsListResponse: 일별 통계 리스트
            - date: 날짜
            - total_asset: 총 자산
            - total_profit_loss: 총 평가손익
            - profit_loss_rate: 수익률 (%)
            - deposit: 예수금
            - stock_evaluation: 주식 평가금액
    """
    stats_service = StatsService(db)
    daily_stats = stats_service.get_daily_stats(current_user.email, days)

    return DailyStatsListResponse(
        success=True,
        data=daily_stats,
        total=len(daily_stats)
    )


@router.get("/monthly", response_model=MonthlyStatsListResponse)
def get_monthly_stats(
    months: int = Query(default=12, ge=1, le=60, description="조회할 월수"),
    current_user: User = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore_db)
):
    """
    월별 자산 통계 조회

    최근 N개월간의 월별 누적 수익금 및 수익률을 Firestore에서 조회합니다.

    Args:
        months: 조회할 월수 (1~60, 기본값: 12)

    Returns:
        MonthlyStatsListResponse: 월별 통계 리스트
            - year_month: 년월 (YYYY-MM)
            - start_asset: 월초 자산
            - end_asset: 월말 자산
            - profit_loss: 월간 손익
            - profit_loss_rate: 월간 수익률 (%)
            - avg_daily_asset: 월평균 자산
    """
    stats_service = StatsService(db)
    monthly_stats = stats_service.get_monthly_stats(current_user.email, months)

    return MonthlyStatsListResponse(
        success=True,
        data=monthly_stats,
        total=len(monthly_stats)
    )


@router.get("/yearly", response_model=YearlyStatsListResponse)
def get_yearly_stats(
    years: int = Query(default=5, ge=1, le=10, description="조회할 연수"),
    current_user: User = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore_db)
):
    """
    연도별 자산 통계 조회

    최근 N년간의 연도별 수익률을 Firestore에서 조회합니다.

    Args:
        years: 조회할 연수 (1~10, 기본값: 5)

    Returns:
        YearlyStatsListResponse: 연도별 통계 리스트
            - year: 연도
            - start_asset: 연초 자산
            - end_asset: 연말 자산
            - profit_loss: 연간 손익
            - profit_loss_rate: 연간 수익률 (%)
            - max_asset: 최고 자산
            - min_asset: 최저 자산
            - avg_monthly_return: 월평균 수익률 (%)
    """
    stats_service = StatsService(db)
    yearly_stats = stats_service.get_yearly_stats(current_user.email, years)

    return YearlyStatsListResponse(
        success=True,
        data=yearly_stats,
        total=len(yearly_stats)
    )
