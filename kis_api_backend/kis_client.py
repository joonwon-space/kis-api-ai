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
