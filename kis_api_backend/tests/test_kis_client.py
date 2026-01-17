import pytest
from httpx import Response
from kis_api_backend.kis_client import KISClient

def test_login_success(httpx_mock):
    """
    Tests successful login to the KIS API.
    """
    httpx_mock.add_response(
        method="POST",
        url="https://openapivts.koreainvestment.com:29443/oauth2/tokenP",
        json={"access_token": "test_token"},
        status_code=200,
    )

    client = KISClient(
        app_key="test_key",
        app_secret="test_secret",
        account_no="test_account",
        acnt_prdt_cd="01",
        is_simulation=True,
    )
    client._get_access_token()
    assert client.access_token == "test_token"

def test_get_balance_success(httpx_mock):
    """
    Tests successful balance inquiry.
    """
    httpx_mock.add_response(
        method="POST",
        url="https://openapivts.koreainvestment.com:29443/oauth2/tokenP",
        json={"access_token": "test_token"},
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://openapivts.koreainvestment.com:29443/uapi/domestic-stock/v1/trading/inquire-balance?CANO=test_account&ACNT_PRDT_CD=01&AFHR_FLPR_YN=N&OFL_YN=&INQR_DVSN=02&UNPR_DVSN=01&FUND_STTL_ICLD_YN=N&FNCG_AMT_AUTO_RDPT_YN=N&PRCS_DVSN=00&CTX_AREA_FK100=&CTX_AREA_NK100=",
        json={
            "output1": [],
            "output2": [
                {
                    "asst_icdc_amt": "1000000",
                    "dnca_tot_amt": "1000000",
                    "evlu_pfls_amt": "0",
                }
            ],
        },
        status_code=200,
    )

    client = KISClient(
        app_key="test_key",
        app_secret="test_secret",
        account_no="test_account",
        acnt_prdt_cd="01",
        is_simulation=True,
    )
    balance = client.get_balance()
    assert balance["total_asset"] == "1000000"
    assert balance["deposit"] == "1000000"
    assert balance["profit_loss"] == "0"
    assert balance["holdings"] == []

def test_get_balance_not_logged_in(httpx_mock):
    """
    Tests balance inquiry without being logged in.
    """
    httpx_mock.add_response(
        method="POST",
        url="https://openapivts.koreainvestment.com:29443/oauth2/tokenP",
        json={"access_token": "test_token"},
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://openapivts.koreainvestment.com:29443/uapi/domestic-stock/v1/trading/inquire-balance?CANO=test_account&ACNT_PRDT_CD=01&AFHR_FLPR_YN=N&OFL_YN=&INQR_DVSN=02&UNPR_DVSN=01&FUND_STTL_ICLD_YN=N&FNCG_AMT_AUTO_RDPT_YN=N&PRCS_DVSN=00&CTX_AREA_FK100=&CTX_AREA_NK100=",
        json={"msg_cd": "EGW00123", "msg1": "Access token is expired."},
        status_code=401,
    )

    client = KISClient(
        app_key="test_key",
        app_secret="test_secret",
        account_no="test_account",
        acnt_prdt_cd="01",
        is_simulation=True,
    )
    with pytest.raises(Exception, match="Failed to get balance"):
        client.get_balance()

def test_login_invalid_credentials(httpx_mock):
    """
    Tests login with invalid credentials.
    """
    httpx_mock.add_response(
        method="POST",
        url="https://openapivts.koreainvestment.com:29443/oauth2/tokenP",
        json={"error_description": "Bad credentials"},
        status_code=401,
    )

    client = KISClient(
        app_key="invalid_key",
        app_secret="invalid_secret",
        account_no="test_account",
        acnt_prdt_cd="01",
        is_simulation=True,
    )
    with pytest.raises(Exception, match="Failed to get access token"):
        client._get_access_token()
