from fastapi import APIRouter, HTTPException, Query
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from kis_client import KISClient
from app.config import settings
from app.schemas.holdings import HoldingsResponse
from app.schemas.common import MarketType
from app.services.account_service import AccountService

router = APIRouter()

# Initialize KIS client with settings
kis_client = KISClient(
    app_key=settings.app_key,
    app_secret=settings.app_secret,
    account_no=settings.account_no,
    acnt_prdt_cd=settings.acnt_prdt_cd,
    is_simulation=settings.is_simulation
)


@router.get("/balance")
def get_balance():
    """
    Fetches the account balance and holdings.

    Returns account balance information including:
    - Total asset value
    - Available deposit
    - Profit/loss
    - List of holdings with details
    """
    try:
        balance_data = kis_client.get_balance()
        return balance_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch balance: {str(e)}")


@router.get("/balance/raw")
def get_balance_raw():
    """
    Returns the raw KIS API response for debugging purposes.
    """
    try:
        access_token = kis_client.token_manager.get_valid_token()
        tr_id = "VTTC8434R" if kis_client.is_simulation else "TTTC8434R"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "appkey": kis_client.app_key,
            "appsecret": kis_client.app_secret,
            "tr_id": tr_id,
            "custtype": "P"
        }
        params = {
            "CANO": kis_client.account_no,
            "ACNT_PRDT_CD": kis_client.acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        url = f"{kis_client.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"

        import httpx
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch raw balance: {str(e)}")


@router.get("/holdings", response_model=HoldingsResponse)
def get_holdings(
    market_type: MarketType = Query(
        default=MarketType.ALL,
        description="시장 구분 (ALL: 전체, DOMESTIC: 국내, OVERSEAS: 해외)"
    )
):
    """
    보유 종목 상세 조회

    국내 및 해외 주식의 보유 현황을 종목별로 상세하게 조회합니다.

    Args:
        market_type: 시장 구분
            - ALL: 국내 + 해외 전체
            - DOMESTIC: 국내 주식만
            - OVERSEAS: 해외 주식만

    Returns:
        HoldingsResponse: 보유 종목 상세 정보
            - market_type: 조회한 시장 구분
            - summary: 요약 정보 (총 평가금액, 손익 등)
            - holdings: 종목별 상세 리스트
    """
    try:
        account_service = AccountService(kis_client)
        return account_service.get_holdings(market_type)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch holdings: {str(e)}"
        )
