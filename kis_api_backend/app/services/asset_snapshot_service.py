"""자산 스냅샷 저장 서비스"""
from datetime import date, datetime
from typing import Optional
from sqlmodel import Session, select
from app.db.models import DailyAsset
from app.schemas.dashboard import DashboardSummary
import logging

logger = logging.getLogger(__name__)


class AssetSnapshotService:
    """자산 스냅샷 관리 서비스"""

    def __init__(self, session: Session):
        self.session = session

    def save_snapshot(
        self,
        user_id: int,
        summary: DashboardSummary,
        snapshot_date: Optional[date] = None
    ) -> DailyAsset:
        """
        자산 스냅샷 저장

        Args:
            user_id: 사용자 ID
            summary: 대시보드 요약 정보
            snapshot_date: 스냅샷 날짜 (기본값: 오늘)

        Returns:
            DailyAsset: 저장된 스냅샷
        """
        if snapshot_date is None:
            snapshot_date = date.today()

        # 기존 스냅샷 확인
        existing = self.get_snapshot(user_id, snapshot_date)
        if existing:
            logger.info(f"Snapshot already exists for user {user_id} on {snapshot_date}")
            return existing

        # 새 스냅샷 생성 (문자열 -> float 변환)
        total_asset = float(summary.total_assets.replace(",", ""))
        total_deposit = float(summary.total_deposit.replace(",", ""))
        total_profit_loss = float(summary.total_profit_loss.replace(",", ""))
        profit_loss_rate = float(summary.profit_loss_rate.replace(",", "")) if summary.profit_loss_rate else 0.0

        # 총 매입금액과 주식 평가금액 계산
        stock_evaluation = total_asset - total_deposit
        total_purchase_amount = stock_evaluation - total_profit_loss

        snapshot = DailyAsset(
            user_id=user_id,
            snapshot_date=snapshot_date,
            total_asset=total_asset,
            total_purchase_amount=total_purchase_amount,
            total_profit_loss=total_profit_loss,
            profit_loss_rate=profit_loss_rate,
            deposit=total_deposit,
            stock_evaluation=stock_evaluation,
        )

        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)

        logger.info(f"Saved snapshot for user {user_id} on {snapshot_date}")
        return snapshot

    def get_snapshot(self, user_id: int, snapshot_date: date) -> Optional[DailyAsset]:
        """
        특정 날짜의 스냅샷 조회

        Args:
            user_id: 사용자 ID
            snapshot_date: 조회할 날짜

        Returns:
            Optional[DailyAsset]: 스냅샷 (없으면 None)
        """
        statement = select(DailyAsset).where(
            DailyAsset.user_id == user_id,
            DailyAsset.snapshot_date == snapshot_date
        )
        return self.session.exec(statement).first()

    def get_snapshots_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> list[DailyAsset]:
        """
        특정 기간의 스냅샷 조회

        Args:
            user_id: 사용자 ID
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            list[DailyAsset]: 스냅샷 리스트 (날짜 오름차순)
        """
        statement = select(DailyAsset).where(
            DailyAsset.user_id == user_id,
            DailyAsset.snapshot_date >= start_date,
            DailyAsset.snapshot_date <= end_date
        ).order_by(DailyAsset.snapshot_date)

        return list(self.session.exec(statement).all())

    def get_latest_snapshot(self, user_id: int) -> Optional[DailyAsset]:
        """
        가장 최근 스냅샷 조회

        Args:
            user_id: 사용자 ID

        Returns:
            Optional[DailyAsset]: 최근 스냅샷 (없으면 None)
        """
        statement = select(DailyAsset).where(
            DailyAsset.user_id == user_id
        ).order_by(DailyAsset.snapshot_date.desc()).limit(1)

        return self.session.exec(statement).first()
