"""주식 관련 API 엔드포인트"""
from fastapi import APIRouter, HTTPException, Query
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from kis_client import KISClient
from app.config import settings
from app.schemas.stock import StockQuote
from app.services.stock_service import StockService

router = APIRouter()

# Initialize KIS client with settings
kis_client = KISClient(
    app_key=settings.app_key,
    app_secret=settings.app_secret,
    account_no=settings.account_no,
    acnt_prdt_cd=settings.acnt_prdt_cd,
    is_simulation=settings.is_simulation
)


@router.get("/quote", response_model=StockQuote)
def get_stock_quote(
    keyword: str = Query(
        ...,
        description="종목명 또는 종목코드/심볼 (예: '삼성전자', '005930', 'AAPL')",
        min_length=1
    )
):
    """
    주식 현재가 조회

    종목명 또는 종목코드/심볼로 주식의 현재가 시세를 조회합니다.

    **국내 주식 예시:**
    - `keyword=삼성전자` → 005930 종목 조회
    - `keyword=005930` → 삼성전자 조회

    **해외 주식 예시:**
    - `keyword=AAPL` → Apple Inc. 조회
    - `keyword=Apple` → Apple Inc. 조회

    Args:
        keyword: 검색 키워드 (종목명, 종목코드, 심볼)

    Returns:
        StockQuote: 현재가 시세 정보
            - market: 시장 구분 (DOMESTIC/OVERSEAS)
            - symbol: 종목코드/심볼
            - name: 종목명
            - current_price: 현재가
            - change: 전일대비
            - change_rate: 등락률(%)
            - change_direction: 등락 방향 (UP/DOWN/UNCHANGED)
            - volume: 거래량
            - open: 시가
            - high: 고가
            - low: 저가
            - currency: 통화 (KRW/USD)
            - updated_at: 조회 시각

    Raises:
        404: 종목을 찾을 수 없음
        500: 시세 조회 실패
    """
    try:
        stock_service = StockService(kis_client)
        return stock_service.get_quote(keyword)
    except ValueError as e:
        # 종목을 찾을 수 없는 경우
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # 기타 에러
        raise HTTPException(
            status_code=500,
            detail=f"시세 조회 실패: {str(e)}"
        )
