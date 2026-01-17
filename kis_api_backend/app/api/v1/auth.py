import os
from fastapi import APIRouter, Depends, HTTPException
from app.schemas import LoginRequest, AuthResponse
from kis_client import KISClient

router = APIRouter()

# This is a simple in-memory storage. Not suitable for production.
# A more robust solution would use a database or a cache like Redis.
kis_clients: dict = {}

@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest):
    """
    Logs in to the KIS API and creates a client instance.
    Credentials can be provided in the request body or as environment variables.
    """
    app_key = request.app_key or os.getenv("APP_KEY")
    app_secret = request.app_secret or os.getenv("APP_SECRET")
    account_no = request.account_no or os.getenv("ACCOUNT_NO")
    acnt_prdt_cd = request.acnt_prdt_cd or os.getenv("ACNT_PRDT_CD")

    if not all([app_key, app_secret, account_no, acnt_prdt_cd]):
        raise HTTPException(
            status_code=400,
            detail="Missing required credentials. Provide them in the request body or as environment variables.",
        )

    try:
        client = KISClient(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            acnt_prdt_cd=acnt_prdt_cd,
            is_simulation=request.is_simulation,
        )
        client._get_access_token()  # Initial token retrieval
        # Use a consistent key for the client, e.g., account_no
        kis_clients[account_no] = client
        return {"message": "Login successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
