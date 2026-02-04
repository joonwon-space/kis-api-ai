import sys
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlmodel import Session

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from kis_client import KISClient
from app.core.deps import get_current_user, get_kis_client
from app.db.models import User
from app.db.database import get_session
from app.schemas.dashboard import DashboardSummary, DashboardHoldingsResponse
from app.services.dashboard_service import DashboardService
from app.services.asset_snapshot_service import AssetSnapshotService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    kis_client: KISClient = Depends(get_kis_client),
    session: Session = Depends(get_session)
):
    """대시보드 요약 정보 조회

    로그인한 사용자의 증권 계좌 요약 정보를 제공합니다.
    조회 시 자동으로 당일 자산 스냅샷을 저장합니다.

    **필요 조건:**
    - JWT 인증 필수
    - 증권사 API 키 등록 필수 (POST /api/v1/user/settings)

    Args:
        current_user: 현재 로그인한 사용자
        kis_client: 사용자별 KIS API 클라이언트
        session: DB 세션

    Returns:
        DashboardSummary: 총 자산, 예수금, 손익, 보유 종목 수

    Raises:
        HTTPException: API 키가 등록되지 않은 경우 400 에러
    """
    service = DashboardService(kis_client)
    summary = service.get_summary()

    # 자산 스냅샷 자동 저장
    try:
        snapshot_service = AssetSnapshotService(session)
        snapshot_service.save_snapshot(current_user.id, summary)
    except Exception as e:
        logger.warning(f"Failed to save snapshot for user {current_user.id}: {e}")
        # 스냅샷 저장 실패해도 대시보드 응답은 정상 반환

    return summary


@router.get("/holdings", response_model=DashboardHoldingsResponse)
def get_dashboard_holdings(
    current_user: User = Depends(get_current_user),
    kis_client: KISClient = Depends(get_kis_client)
):
    """대시보드 보유 종목 조회

    요약 정보와 함께 보유 종목 상세 리스트를 제공합니다.

    **필요 조건:**
    - JWT 인증 필수
    - 증권사 API 키 등록 필수 (POST /api/v1/user/settings)

    Args:
        current_user: 현재 로그인한 사용자
        kis_client: 사용자별 KIS API 클라이언트

    Returns:
        DashboardHoldingsResponse: 요약 + 종목 리스트

    Raises:
        HTTPException: API 키가 등록되지 않은 경우 400 에러
    """
    service = DashboardService(kis_client)
    return service.get_holdings_with_summary()
