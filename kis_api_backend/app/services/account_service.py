"""계좌 관련 비즈니스 로직"""
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.schemas.holdings import HoldingsResponse, HoldingItem, HoldingsSummary
from app.schemas.common import MarketType, Currency
from kis_client import KISClient


class AccountService:
    """계좌 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    def __init__(self, kis_client: KISClient):
        self.kis_client = kis_client

    def get_holdings(self, market_type: MarketType = MarketType.ALL) -> HoldingsResponse:
        """
        보유 종목 조회 (통합)

        Args:
            market_type: 시장 구분 (ALL/DOMESTIC/OVERSEAS)

        Returns:
            HoldingsResponse: 통합 포트폴리오 데이터
        """
        holdings = []

        if market_type in [MarketType.ALL, MarketType.DOMESTIC]:
            try:
                domestic_data = self.kis_client.get_domestic_holdings()
                holdings.extend(self._parse_domestic_holdings(domestic_data))
            except Exception as e:
                # 국내 주식 조회 실패 시 로깅만 하고 계속 진행
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to get domestic holdings: {e}")

        if market_type in [MarketType.ALL, MarketType.OVERSEAS]:
            try:
                overseas_data = self.kis_client.get_overseas_holdings()
                holdings.extend(self._parse_overseas_holdings(overseas_data))
            except Exception as e:
                # 해외 주식 조회 실패 시 로깅만 하고 계속 진행
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to get overseas holdings: {e}")

        summary = self._calculate_summary(holdings, market_type)

        return HoldingsResponse(
            market_type=market_type,
            summary=summary,
            holdings=holdings
        )

    def _parse_domestic_holdings(self, data: Dict[str, Any]) -> List[HoldingItem]:
        """
        국내 주식 데이터 파싱

        Args:
            data: KIS API 원본 응답

        Returns:
            List[HoldingItem]: 파싱된 보유 종목 리스트
        """
        holdings = []
        output1 = data.get("output1", [])

        if not output1:
            return holdings

        for item in output1:
            # 보유수량이 0이거나 없으면 스킵
            quantity = item.get("hldg_qty", "0")
            if not quantity or quantity == "0":
                continue

            holding = HoldingItem(
                market="DOMESTIC",
                symbol=item.get("pdno", ""),
                name=item.get("prdt_name", ""),
                quantity=quantity,
                avg_price=item.get("pchs_avg_pric", "0"),
                current_price=item.get("prpr", "0"),
                evaluation_amount=item.get("evlu_amt", "0"),
                profit_loss=item.get("evlu_pfls_amt", "0"),
                profit_loss_rate=item.get("evlu_pfls_rt", "0"),
                currency=Currency.KRW
            )
            holdings.append(holding)

        return holdings

    def _parse_overseas_holdings(self, data: Dict[str, Any]) -> List[HoldingItem]:
        """
        해외 주식 데이터 파싱

        Args:
            data: KIS API 원본 응답

        Returns:
            List[HoldingItem]: 파싱된 보유 종목 리스트
        """
        holdings = []
        output1 = data.get("output1", [])

        if not output1:
            return holdings

        for item in output1:
            # 보유수량이 0이거나 없으면 스킵
            quantity = item.get("ovrs_cblc_qty", "0")
            if not quantity or quantity == "0":
                continue

            # 평균 매입가 계산 (매입금액 / 수량)
            purchase_amt = float(item.get("frcr_pchs_amt1", "0"))
            qty = float(quantity)
            avg_price = str(round(purchase_amt / qty, 2)) if qty > 0 else "0"

            holding = HoldingItem(
                market="OVERSEAS",
                symbol=item.get("ovrs_pdno", ""),
                name=item.get("ovrs_item_name", ""),
                quantity=quantity,
                avg_price=avg_price,
                current_price=item.get("now_pric2", "0"),
                evaluation_amount=item.get("ovrs_stck_evlu_amt", "0"),
                profit_loss=item.get("frcr_evlu_pfls_amt", "0"),
                profit_loss_rate=item.get("evlu_pfls_rt", "0"),
                currency=Currency.USD
            )
            holdings.append(holding)

        return holdings

    def _calculate_summary(
        self,
        holdings: List[HoldingItem],
        market_type: MarketType
    ) -> HoldingsSummary:
        """
        보유 종목 요약 계산

        Args:
            holdings: 보유 종목 리스트
            market_type: 시장 구분

        Returns:
            HoldingsSummary: 요약 정보
        """
        if not holdings:
            return HoldingsSummary(
                total_evaluation="0",
                total_purchase="0",
                total_profit_loss="0",
                profit_loss_rate="0"
            )

        # 통화별로 분리하여 계산 (국내: KRW, 해외: USD)
        # 단순화를 위해 국내 주식만 합산 (통화가 다르면 직접 합산 불가)
        if market_type == MarketType.DOMESTIC:
            domestic_holdings = [h for h in holdings if h.currency == Currency.KRW]
            return self._calculate_krw_summary(domestic_holdings)
        elif market_type == MarketType.OVERSEAS:
            overseas_holdings = [h for h in holdings if h.currency == Currency.USD]
            return self._calculate_usd_summary(overseas_holdings)
        else:  # ALL
            # 통화가 혼재된 경우 요약 정보는 제공하지 않음
            return HoldingsSummary(
                total_evaluation=None,
                total_purchase=None,
                total_profit_loss=None,
                profit_loss_rate=None
            )

    def _calculate_krw_summary(self, holdings: List[HoldingItem]) -> HoldingsSummary:
        """KRW 통화 요약 계산"""
        total_evaluation = sum(float(h.evaluation_amount) for h in holdings)
        total_profit_loss = sum(float(h.profit_loss) for h in holdings)
        total_purchase = total_evaluation - total_profit_loss

        profit_loss_rate = "0"
        if total_purchase > 0:
            profit_loss_rate = str(round((total_profit_loss / total_purchase) * 100, 2))

        return HoldingsSummary(
            total_evaluation=str(int(total_evaluation)),
            total_purchase=str(int(total_purchase)),
            total_profit_loss=str(int(total_profit_loss)),
            profit_loss_rate=profit_loss_rate
        )

    def _calculate_usd_summary(self, holdings: List[HoldingItem]) -> HoldingsSummary:
        """USD 통화 요약 계산"""
        total_evaluation = sum(float(h.evaluation_amount) for h in holdings)
        total_profit_loss = sum(float(h.profit_loss) for h in holdings)
        total_purchase = total_evaluation - total_profit_loss

        profit_loss_rate = "0"
        if total_purchase > 0:
            profit_loss_rate = str(round((total_profit_loss / total_purchase) * 100, 2))

        return HoldingsSummary(
            total_evaluation=str(round(total_evaluation, 2)),
            total_purchase=str(round(total_purchase, 2)),
            total_profit_loss=str(round(total_profit_loss, 2)),
            profit_loss_rate=profit_loss_rate
        )
