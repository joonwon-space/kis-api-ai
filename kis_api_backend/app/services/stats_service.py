"""통계 계산 서비스"""
from datetime import date, timedelta
from collections import defaultdict
from sqlmodel import Session
from app.services.asset_snapshot_service import AssetSnapshotService
from app.schemas.stats import (
    DailyAssetResponse,
    MonthlyStatResponse,
    YearlyStatResponse
)
import logging

logger = logging.getLogger(__name__)


class StatsService:
    """통계 계산 서비스"""

    def __init__(self, session: Session):
        self.session = session
        self.snapshot_service = AssetSnapshotService(session)

    def get_daily_stats(self, user_id: int, days: int = 30) -> list[DailyAssetResponse]:
        """
        일별 통계 조회

        Args:
            user_id: 사용자 ID
            days: 조회할 일수 (기본 30일)

        Returns:
            list[DailyAssetResponse]: 일별 통계 리스트
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        snapshots = self.snapshot_service.get_snapshots_range(
            user_id, start_date, end_date
        )

        return [
            DailyAssetResponse(
                date=snapshot.snapshot_date,
                total_asset=snapshot.total_asset,
                total_profit_loss=snapshot.total_profit_loss,
                profit_loss_rate=snapshot.profit_loss_rate,
                deposit=snapshot.deposit,
                stock_evaluation=snapshot.stock_evaluation
            )
            for snapshot in snapshots
        ]

    def get_monthly_stats(self, user_id: int, months: int = 12) -> list[MonthlyStatResponse]:
        """
        월별 통계 조회

        Args:
            user_id: 사용자 ID
            months: 조회할 월수 (기본 12개월)

        Returns:
            list[MonthlyStatResponse]: 월별 통계 리스트
        """
        end_date = date.today()
        # 12개월 전으로 시작 날짜 설정
        start_date = date(end_date.year, end_date.month, 1) - timedelta(days=30 * (months - 1))
        start_date = date(start_date.year, start_date.month, 1)  # 월초로 조정

        snapshots = self.snapshot_service.get_snapshots_range(
            user_id, start_date, end_date
        )

        if not snapshots:
            return []

        # 월별로 그룹화
        monthly_data = defaultdict(list)
        for snapshot in snapshots:
            year_month = snapshot.snapshot_date.strftime("%Y-%m")
            monthly_data[year_month].append(snapshot)

        # 월별 통계 계산
        result = []
        for year_month in sorted(monthly_data.keys()):
            month_snapshots = monthly_data[year_month]
            start_asset = month_snapshots[0].total_asset
            end_asset = month_snapshots[-1].total_asset
            profit_loss = end_asset - start_asset
            profit_loss_rate = (profit_loss / start_asset * 100) if start_asset > 0 else 0.0
            avg_daily_asset = sum(s.total_asset for s in month_snapshots) / len(month_snapshots)

            result.append(MonthlyStatResponse(
                year_month=year_month,
                start_asset=start_asset,
                end_asset=end_asset,
                profit_loss=profit_loss,
                profit_loss_rate=round(profit_loss_rate, 2),
                avg_daily_asset=round(avg_daily_asset, 2)
            ))

        return result

    def get_yearly_stats(self, user_id: int, years: int = 5) -> list[YearlyStatResponse]:
        """
        연도별 통계 조회

        Args:
            user_id: 사용자 ID
            years: 조회할 연수 (기본 5년)

        Returns:
            list[YearlyStatResponse]: 연도별 통계 리스트
        """
        end_date = date.today()
        start_date = date(end_date.year - years + 1, 1, 1)

        snapshots = self.snapshot_service.get_snapshots_range(
            user_id, start_date, end_date
        )

        if not snapshots:
            return []

        # 연도별로 그룹화
        yearly_data = defaultdict(list)
        for snapshot in snapshots:
            year = snapshot.snapshot_date.year
            yearly_data[year].append(snapshot)

        # 연도별 통계 계산
        result = []
        for year in sorted(yearly_data.keys()):
            year_snapshots = yearly_data[year]
            start_asset = year_snapshots[0].total_asset
            end_asset = year_snapshots[-1].total_asset
            profit_loss = end_asset - start_asset
            profit_loss_rate = (profit_loss / start_asset * 100) if start_asset > 0 else 0.0

            # 최고/최저 자산
            max_asset = max(s.total_asset for s in year_snapshots)
            min_asset = min(s.total_asset for s in year_snapshots)

            # 월평균 수익률 계산 (월별로 집계)
            monthly_returns = []
            month_data = defaultdict(list)
            for snapshot in year_snapshots:
                month = snapshot.snapshot_date.month
                month_data[month].append(snapshot)

            for month in sorted(month_data.keys()):
                month_snapshots = month_data[month]
                month_start = month_snapshots[0].total_asset
                month_end = month_snapshots[-1].total_asset
                if month_start > 0:
                    month_return = (month_end - month_start) / month_start * 100
                    monthly_returns.append(month_return)

            avg_monthly_return = sum(monthly_returns) / len(monthly_returns) if monthly_returns else 0.0

            result.append(YearlyStatResponse(
                year=year,
                start_asset=start_asset,
                end_asset=end_asset,
                profit_loss=profit_loss,
                profit_loss_rate=round(profit_loss_rate, 2),
                max_asset=max_asset,
                min_asset=min_asset,
                avg_monthly_return=round(avg_monthly_return, 2)
            ))

        return result
