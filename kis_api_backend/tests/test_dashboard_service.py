"""대시보드 서비스 테스트"""

import pytest
from unittest.mock import Mock, MagicMock
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardSummary, DashboardHoldingsResponse


@pytest.fixture
def mock_kis_client():
    """Mock KIS Client"""
    client = Mock()

    # Mock balance data (KIS API 응답 형식)
    client.get_balance.return_value = {
        "output1": [
            {
                "pdno": "005930",
                "prdt_name": "삼성전자",
                "hldg_qty": "10",
                "pchs_avg_pric": "70000",
                "prpr": "75000",
                "evlu_amt": "750000",
                "evlu_pfls_amt": "50000",
                "evlu_pfls_rt": "7.14"
            },
            {
                "pdno": "000660",
                "prdt_name": "SK하이닉스",
                "hldg_qty": "5",
                "pchs_avg_pric": "100000",
                "prpr": "110000",
                "evlu_amt": "550000",
                "evlu_pfls_amt": "50000",
                "evlu_pfls_rt": "10.00"
            }
        ],
        "output2": [
            {
                "tot_evlu_amt": "1300000",  # 총 평가액
                "dnca_tot_amt": "200000",   # 예수금
                "evlu_pfls_smtl_amt": "100000"  # 총 손익
            }
        ]
    }

    return client


class TestDashboardService:
    """DashboardService 단위 테스트"""

    def test_get_summary(self, mock_kis_client):
        """요약 정보 조회 테스트"""
        service = DashboardService(mock_kis_client)
        summary = service.get_summary()

        assert isinstance(summary, DashboardSummary)
        assert summary.total_assets == "1300000"
        assert summary.total_deposit == "200000"
        assert summary.total_profit_loss == "100000"
        assert summary.stock_count == 2
        assert summary.profit_loss_rate is not None

    def test_get_summary_calculates_profit_rate(self, mock_kis_client):
        """수익률 계산 테스트"""
        service = DashboardService(mock_kis_client)
        summary = service.get_summary()

        # 수익률 = (손익 / 매입가) * 100
        # 매입가 = 총평가액 - 손익 = 1300000 - 100000 = 1200000
        # 수익률 = (100000 / 1200000) * 100 = 8.33
        assert summary.profit_loss_rate is not None
        profit_rate = float(summary.profit_loss_rate)
        assert 8.0 < profit_rate < 9.0

    def test_get_summary_no_stocks(self):
        """보유 종목이 없을 때 요약 정보"""
        client = Mock()
        client.get_balance.return_value = {
            "output1": [],
            "output2": [
                {
                    "tot_evlu_amt": "0",
                    "dnca_tot_amt": "1000000",
                    "evlu_pfls_smtl_amt": "0"
                }
            ]
        }

        service = DashboardService(client)
        summary = service.get_summary()

        assert summary.stock_count == 0
        assert summary.total_assets == "0"
        assert summary.total_deposit == "1000000"

    def test_get_holdings_with_summary(self, mock_kis_client):
        """보유 종목 + 요약 조회 테스트"""
        service = DashboardService(mock_kis_client)
        response = service.get_holdings_with_summary()

        assert isinstance(response, DashboardHoldingsResponse)
        assert response.summary is not None
        assert isinstance(response.holdings, list)
        assert len(response.holdings) == 2

    def test_parse_holdings(self, mock_kis_client):
        """보유 종목 파싱 테스트"""
        service = DashboardService(mock_kis_client)
        response = service.get_holdings_with_summary()

        # 첫 번째 종목 확인
        holding = response.holdings[0]
        assert holding.symbol == "005930"
        assert holding.name == "삼성전자"
        assert holding.quantity == "10"
        assert holding.market == "DOMESTIC"
        assert holding.currency == "KRW"

    def test_parse_holdings_filters_zero_quantity(self):
        """보유수량 0인 종목 필터링 테스트"""
        client = Mock()
        client.get_balance.return_value = {
            "output1": [
                {
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "hldg_qty": "10",
                    "pchs_avg_pric": "70000",
                    "prpr": "75000",
                    "evlu_amt": "750000",
                    "evlu_pfls_amt": "50000",
                    "evlu_pfls_rt": "7.14"
                },
                {
                    "pdno": "000660",
                    "prdt_name": "SK하이닉스",
                    "hldg_qty": "0",  # 보유수량 0
                    "pchs_avg_pric": "100000",
                    "prpr": "110000",
                    "evlu_amt": "0",
                    "evlu_pfls_amt": "0",
                    "evlu_pfls_rt": "0"
                }
            ],
            "output2": [
                {
                    "tot_evlu_amt": "750000",
                    "dnca_tot_amt": "200000",
                    "evlu_pfls_smtl_amt": "50000"
                }
            ]
        }

        service = DashboardService(client)
        response = service.get_holdings_with_summary()

        # 보유수량 0인 종목은 제외되어야 함
        assert len(response.holdings) == 1
        assert response.holdings[0].symbol == "005930"

    def test_get_summary_with_dict_output2(self):
        """output2가 dict일 때 처리 테스트"""
        client = Mock()
        client.get_balance.return_value = {
            "output1": [],
            "output2": {  # list가 아닌 dict
                "tot_evlu_amt": "1000000",
                "dnca_tot_amt": "500000",
                "evlu_pfls_smtl_amt": "100000"
            }
        }

        service = DashboardService(client)
        summary = service.get_summary()

        # dict도 정상 처리되어야 함
        assert summary.total_assets == "1000000"
        assert summary.total_deposit == "500000"
