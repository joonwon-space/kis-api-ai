import requests
import json
from typing import Dict, Any

class KISClient:
    """
    Client for interacting with the Korea Investment & Securities (KIS) Open API.
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
        self.access_token = None

    def _get_access_token(self) -> None:
        """
        Retrieves an access token from the KIS API.
        """
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }
        url = f"{self.base_url}/oauth2/tokenP"
        try:
            response = requests.post(url, headers=headers, data=json.dumps(body))
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get access token: {e}")

    def get_balance(self) -> Dict[str, Any]:
        """
        Fetches the account balance and holdings.

        Returns:
            Dict[str, Any]: A dictionary containing total asset value, deposit, profit/loss, and holdings.
        """
        if not self.access_token:
            self._get_access_token()

        tr_id = "VTTC8434R" if self.is_simulation else "TTTC8434R"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
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
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            # The actual parsing logic will depend on the exact structure of the KIS API response.
            # This is a placeholder based on the user's request.
            total_asset = data.get("output2", [{}])[0].get("asst_icdc_amt")
            deposit = data.get("output2", [{}])[0].get("dnca_tot_amt")
            profit_loss = data.get("output2", [{}])[0].get("evlu_pfls_amt")
            
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

        except requests.exceptions.RequestException as e:
            # If the token is expired, the API might return a specific error code.
            # Here we can check for that and try to refresh the token.
            # For now, we'll just raise a generic exception.
            raise Exception(f"Failed to get balance: {e}")
