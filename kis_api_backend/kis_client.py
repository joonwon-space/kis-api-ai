import httpx
from typing import Dict, Any
import sys
from pathlib import Path

# Add parent directory to path to import from app
sys.path.append(str(Path(__file__).parent))

from app.services.token_manager import TokenManager


class KISClient:
    """
    Client for interacting with the Korea Investment & Securities (KIS) Open API.

    Uses TokenManager to efficiently manage access tokens with caching and automatic renewal.
    """

    def __init__(self, app_key: str, app_secret: str, account_no: str, acnt_prdt_cd: str, is_simulation: bool = True):
        """
        Initializes the KISClient.

        Args:
            app_key (str): The application key issued by KIS.
            app_secret (str): The application secret issued by KIS.
            account_no (str): The account number (8 digits).
            acnt_prdt_cd (str): The account product code (2 digits).
            is_simulation (bool): True for simulation trading, False for real trading.
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_no = account_no
        self.acnt_prdt_cd = acnt_prdt_cd
        self.is_simulation = is_simulation
        self.base_url = "https://openapivts.koreainvestment.com:29443" if is_simulation else "https://openapi.koreainvestment.com:9443"

        # Initialize TokenManager for efficient token management
        self.token_manager = TokenManager(
            app_key=app_key,
            app_secret=app_secret,
            base_url=self.base_url
        )

    def get_balance(self) -> Dict[str, Any]:
        """
        Fetches the account balance and holdings.

        Returns:
            Dict[str, Any]: A dictionary containing total asset value, deposit, profit/loss, and holdings.
        """
        # Get valid token (automatically renewed if expired)
        access_token = self.token_manager.get_valid_token()

        tr_id = "VTTC8434R" if self.is_simulation else "TTTC8434R"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P"
        }
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
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
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        try:
            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

            # Log the raw response for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"KIS API Response: {data}")

            # The actual parsing logic will depend on the exact structure of the KIS API response.
            # This is a placeholder based on the user's request.
            output2 = data.get("output2", [])
            if isinstance(output2, list) and len(output2) > 0:
                total_asset = output2[0].get("asst_icdc_amt")
                deposit = output2[0].get("dnca_tot_amt")
                profit_loss = output2[0].get("evlu_pfls_amt")
            else:
                # output2 might be a dict instead of list
                total_asset = output2.get("asst_icdc_amt") if isinstance(output2, dict) else None
                deposit = output2.get("dnca_tot_amt") if isinstance(output2, dict) else None
                profit_loss = output2.get("evlu_pfls_amt") if isinstance(output2, dict) else None
            
            holdings = []
            if "output1" in data and data["output1"]:
                for item in data["output1"]:
                    holdings.append({
                        "name": item.get("prdt_name"),
                        "current_price": item.get("prpr"),
                        "quantity": item.get("hldg_qty"),
                        "profit_loss_rate": item.get("evlu_pfls_rt")
                    })

            return {
                "total_asset": total_asset,
                "deposit": deposit,
                "profit_loss": profit_loss,
                "holdings": holdings,
            }

        except httpx.HTTPStatusError as e:
            # Log the response body for debugging
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            raise Exception(f"Failed to get balance: {e}\nResponse: {error_detail}")
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get balance: {e}")

    def get_domestic_holdings(self) -> Dict[str, Any]:
        """
        국내 주식 보유 내역 상세 조회

        Returns:
            Dict[str, Any]: KIS API 원본 응답 (output1: 보유 종목, output2: 계좌 요약)
        """
        access_token = self.token_manager.get_valid_token()

        tr_id = "VTTC8434R" if self.is_simulation else "TTTC8434R"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P"
        }
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",  # 종목별 조회
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"

        try:
            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            raise Exception(f"Failed to get domestic holdings: {e}\nResponse: {error_detail}")
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get domestic holdings: {e}")

    def get_overseas_holdings(self, exchange_code: str = "NASD") -> Dict[str, Any]:
        """
        해외 주식 보유 내역 조회

        Args:
            exchange_code (str): 거래소 코드 (NASD: 나스닥, NYSE: 뉴욕, AMEX: 아멕스)

        Returns:
            Dict[str, Any]: KIS API 원본 응답
        """
        access_token = self.token_manager.get_valid_token()

        tr_id = "JTTT3012R" if self.is_simulation else "TTTS3012R"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P"
        }
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": exchange_code,
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"

        try:
            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            raise Exception(f"Failed to get overseas holdings: {e}\nResponse: {error_detail}")
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get overseas holdings: {e}")

    def get_domestic_stock_price(self, stock_code: str) -> Dict[str, Any]:
        """
        국내 주식 현재가 조회

        Args:
            stock_code (str): 종목코드 (6자리)

        Returns:
            Dict[str, Any]: KIS API 원본 응답
        """
        access_token = self.token_manager.get_valid_token()

        tr_id = "FHKST01010100"  # 실전/모의 동일
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P"
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # J:주식
            "FID_INPUT_ISCD": stock_code
        }
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"

        try:
            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            raise Exception(f"Failed to get domestic stock price: {e}\nResponse: {error_detail}")
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get domestic stock price: {e}")

    def get_overseas_stock_price(self, symbol: str, exchange_code: str = "NAS") -> Dict[str, Any]:
        """
        해외 주식 현재가 조회

        Args:
            symbol (str): 심볼 (예: AAPL)
            exchange_code (str): 거래소 코드 (NAS:나스닥, NYS:뉴욕, AMS:아멕스)

        Returns:
            Dict[str, Any]: KIS API 원본 응답
        """
        access_token = self.token_manager.get_valid_token()

        tr_id = "HHDFS00000300"  # 실전/모의 동일
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P"
        }
        params = {
            "AUTH": "",
            "EXCD": exchange_code,
            "SYMB": symbol
        }
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"

        try:
            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            raise Exception(f"Failed to get overseas stock price: {e}\nResponse: {error_detail}")
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get overseas stock price: {e}")
