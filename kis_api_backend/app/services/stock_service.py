"""주식 검색 및 시세 조회 서비스"""
import sys
from pathlib import Path
from typing import Dict
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.schemas.stock import StockQuote
from app.schemas.common import Currency
from app.services.stock_master_service import stock_master_service
from kis_client import KISClient


class StockService:
    """주식 검색 및 시세 조회 서비스"""

    def __init__(self, kis_client: KISClient):
        self.kis_client = kis_client
        self.master_service = stock_master_service

    def get_quote(self, keyword: str) -> StockQuote:
        """
        주식 현재가 조회

        Args:
            keyword: 종목명 또는 코드/심볼

        Returns:
            StockQuote: 현재가 시세 정보

        Raises:
            ValueError: 종목을 찾을 수 없는 경우
        """
        # 1. 종목 검색 (캐시)
        stock = self.master_service.search(keyword)

        # 2. 캐시에 없으면 종목코드인지 확인 (6자리 숫자)
        if not stock and keyword.isdigit() and len(keyword) == 6:
            # 종목코드로 직접 조회 (캐시 없이)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Direct query for stock code: {keyword}")
            stock = {
                "market": "DOMESTIC",
                "code": keyword,
                "name": keyword  # 종목명은 응답에서 가져올 수 있으면 업데이트
            }

        # 3. 여전히 못 찾으면 에러
        if not stock:
            raise ValueError(f"종목을 찾을 수 없습니다: {keyword}")

        # 4. 시세 조회
        if stock["market"] == "DOMESTIC":
            return self._get_domestic_quote(stock)
        else:
            return self._get_overseas_quote(stock)

    def _get_domestic_quote(self, stock: Dict) -> StockQuote:
        """
        국내 주식 현재가 조회

        Args:
            stock: 종목 정보

        Returns:
            StockQuote: 시세 정보
        """
        code = stock["code"]
        data = self.kis_client.get_domestic_stock_price(code)

        # KIS API 응답 파싱
        output = data.get("output", {})

        # 전일대비 부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
        sign = output.get("prdy_vrss_sign", "3")
        if sign in ["1", "2"]:
            direction = "UP"
        elif sign in ["4", "5"]:
            direction = "DOWN"
        else:
            direction = "UNCHANGED"

        return StockQuote(
            market="DOMESTIC",
            symbol=code,
            name=stock["name"],
            current_price=output.get("stck_prpr", "0"),
            change=output.get("prdy_vrss", "0"),
            change_rate=output.get("prdy_ctrt", "0"),
            change_direction=direction,
            volume=output.get("acml_vol", "0"),
            open=output.get("stck_oprc", "0"),
            high=output.get("stck_hgpr", "0"),
            low=output.get("stck_lwpr", "0"),
            currency=Currency.KRW,
            updated_at=datetime.now().isoformat()
        )

    def _get_overseas_quote(self, stock: Dict) -> StockQuote:
        """
        해외 주식 현재가 조회

        Args:
            stock: 종목 정보

        Returns:
            StockQuote: 시세 정보
        """
        symbol = stock["symbol"]
        exchange = stock.get("exchange", "NASD")

        # 거래소 코드 변환 (NASD -> NAS)
        exchange_code = "NAS" if exchange == "NASD" else exchange[:3]

        data = self.kis_client.get_overseas_stock_price(symbol, exchange_code)

        # KIS API 응답 파싱
        output = data.get("output", {})

        # 등락 판단
        change = output.get("diff", "0")
        try:
            change_float = float(change)
            if change_float > 0:
                direction = "UP"
            elif change_float < 0:
                direction = "DOWN"
            else:
                direction = "UNCHANGED"
        except:
            direction = "UNCHANGED"

        return StockQuote(
            market="OVERSEAS",
            symbol=symbol,
            name=stock["name"],
            current_price=output.get("last", "0"),
            change=str(abs(float(change))) if change else "0",
            change_rate=output.get("rate", "0"),
            change_direction=direction,
            volume=output.get("tvol", "0"),
            open=output.get("open", "0"),
            high=output.get("high", "0"),
            low=output.get("low", "0"),
            currency=Currency.USD,
            updated_at=datetime.now().isoformat()
        )
