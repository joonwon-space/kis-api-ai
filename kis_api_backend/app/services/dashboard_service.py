import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from kis_client import KISClient
from app.schemas.dashboard import DashboardSummary, DashboardHoldingsResponse
from app.schemas.holdings import HoldingItem


class DashboardService:
    """대시보드 데이터 제공 서비스"""

    def __init__(self, kis_client: KISClient):
        self.kis_client = kis_client

    def get_summary(self) -> DashboardSummary:
        """대시보드 요약 정보 조회

        Returns:
            DashboardSummary: 총 자산, 예수금, 손익 등
        """
        # KIS API 잔고 조회 (TTTC8434R)
        balance_data = self.kis_client.get_balance()

        # output2에서 요약 정보 추출
        output2 = balance_data.get("output2", {})
        if isinstance(output2, list) and len(output2) > 0:
            output2 = output2[0]

        # output1에서 종목 수 계산
        output1 = balance_data.get("output1", [])
        stock_count = len([item for item in output1 if item.get("hldg_qty", "0") != "0"])

        total_assets = output2.get("tot_evlu_amt", "0")
        total_deposit = output2.get("dnca_tot_amt", "0")
        total_profit_loss = output2.get("evlu_pfls_smtl_amt", "0")

        # 수익률 계산
        profit_loss_rate = None
        if total_assets and total_profit_loss:
            try:
                assets = float(total_assets)
                profit = float(total_profit_loss)
                purchase = assets - profit
                if purchase > 0:
                    profit_loss_rate = str(round((profit / purchase) * 100, 2))
            except (ValueError, ZeroDivisionError):
                pass

        return DashboardSummary(
            total_assets=total_assets,
            total_deposit=total_deposit,
            total_profit_loss=total_profit_loss,
            profit_loss_rate=profit_loss_rate,
            stock_count=stock_count
        )

    def get_holdings_with_summary(self) -> DashboardHoldingsResponse:
        """보유 종목 + 요약 정보 조회

        Returns:
            DashboardHoldingsResponse: 요약 + 종목 리스트
        """
        balance_data = self.kis_client.get_balance()
        summary = self.get_summary()

        # 보유 종목 파싱
        output1 = balance_data.get("output1", [])
        holdings = self._parse_holdings(output1)

        return DashboardHoldingsResponse(
            summary=summary,
            holdings=holdings
        )

    def _parse_holdings(self, output1: List[Dict[str, Any]]) -> List[HoldingItem]:
        """보유 종목 파싱

        Args:
            output1: KIS API output1 데이터

        Returns:
            List[HoldingItem]: 파싱된 보유 종목 리스트
        """
        holdings = []

        for item in output1:
            quantity = item.get("hldg_qty", "0")
            if quantity == "0":
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
                currency="KRW"
            )
            holdings.append(holding)

        return holdings
