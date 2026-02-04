"""자산 스냅샷 저장 서비스 (Firestore 기반)"""
from datetime import date, datetime
from typing import Optional
from google.cloud import firestore
from app.schemas.dashboard import DashboardSummary
import logging

logger = logging.getLogger(__name__)


class AssetSnapshotService:
    """자산 스냅샷 관리 서비스 (Firestore 기반)

    Firestore 구조:
        daily_assets/{email}_{YYYY-MM-DD}
    """

    def __init__(self, db: firestore.Client):
        self.db = db
        self.collection = db.collection("daily_assets")

    def _get_doc_id(self, user_email: str, snapshot_date: date) -> str:
        """
        Document ID 생성: {email}_{YYYY-MM-DD}

        Args:
            user_email: 사용자 이메일
            snapshot_date: 스냅샷 날짜

        Returns:
            str: Document ID
        """
        return f"{user_email}_{snapshot_date.isoformat()}"

    def save_snapshot(
        self,
        user_email: str,
        summary: DashboardSummary,
        snapshot_date: Optional[date] = None
    ) -> dict:
        """
        자산 스냅샷 저장

        Args:
            user_email: 사용자 이메일
            summary: 대시보드 요약 정보
            snapshot_date: 스냅샷 날짜 (기본값: 오늘)

        Returns:
            dict: 저장된 스냅샷 데이터
        """
        if snapshot_date is None:
            snapshot_date = date.today()

        doc_id = self._get_doc_id(user_email, snapshot_date)
        doc_ref = self.collection.document(doc_id)

        # 기존 스냅샷 확인
        doc = doc_ref.get()
        if doc.exists:
            logger.info(f"Snapshot already exists for {user_email} on {snapshot_date}")
            return doc.to_dict()

        # 새 스냅샷 생성 (문자열 -> float 변환)
        total_asset = float(summary.total_assets.replace(",", ""))
        total_deposit = float(summary.total_deposit.replace(",", ""))
        total_profit_loss = float(summary.total_profit_loss.replace(",", ""))
        profit_loss_rate = float(summary.profit_loss_rate.replace(",", "")) if summary.profit_loss_rate else 0.0

        # 총 매입금액과 주식 평가금액 계산
        stock_evaluation = total_asset - total_deposit
        total_purchase_amount = stock_evaluation - total_profit_loss

        snapshot_data = {
            "user_email": user_email,
            "snapshot_date": snapshot_date.isoformat(),
            "total_asset": total_asset,
            "total_purchase_amount": total_purchase_amount,
            "total_profit_loss": total_profit_loss,
            "profit_loss_rate": profit_loss_rate,
            "deposit": total_deposit,
            "stock_evaluation": stock_evaluation,
            "created_at": datetime.utcnow().isoformat(),
        }

        doc_ref.set(snapshot_data)

        logger.info(f"Saved snapshot for {user_email} on {snapshot_date}")
        return snapshot_data

    def get_snapshot(self, user_email: str, snapshot_date: date) -> Optional[dict]:
        """
        특정 날짜의 스냅샷 조회

        Args:
            user_email: 사용자 이메일
            snapshot_date: 조회할 날짜

        Returns:
            Optional[dict]: 스냅샷 데이터 (없으면 None)
        """
        doc_id = self._get_doc_id(user_email, snapshot_date)
        doc = self.collection.document(doc_id).get()

        if not doc.exists:
            return None

        return doc.to_dict()

    def get_snapshots_range(
        self,
        user_email: str,
        start_date: date,
        end_date: date
    ) -> list[dict]:
        """
        특정 기간의 스냅샷 조회

        Args:
            user_email: 사용자 이메일
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            list[dict]: 스냅샷 리스트 (날짜 오름차순)
        """
        # Firestore 쿼리: user_email과 날짜 범위로 필터링
        query = (
            self.collection
            .where("user_email", "==", user_email)
            .where("snapshot_date", ">=", start_date.isoformat())
            .where("snapshot_date", "<=", end_date.isoformat())
            .order_by("snapshot_date")
        )

        docs = query.stream()
        return [doc.to_dict() for doc in docs]

    def get_latest_snapshot(self, user_email: str) -> Optional[dict]:
        """
        가장 최근 스냅샷 조회

        Args:
            user_email: 사용자 이메일

        Returns:
            Optional[dict]: 최근 스냅샷 (없으면 None)
        """
        # Firestore 쿼리: user_email 필터, snapshot_date 내림차순, limit 1
        query = (
            self.collection
            .where("user_email", "==", user_email)
            .order_by("snapshot_date", direction=firestore.Query.DESCENDING)
            .limit(1)
        )

        docs = list(query.stream())
        if not docs:
            return None

        return docs[0].to_dict()
