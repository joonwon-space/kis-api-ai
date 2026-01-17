from fastapi import APIRouter, HTTPException, Path
from app.schemas import BalanceResponse
from app.api.v1.auth import kis_clients  # Import the in-memory storage

router = APIRouter()

@router.get("/balance/{account_no}", response_model=BalanceResponse)
def get_balance(account_no: str = Path(..., title="Account Number")):
    """
    Fetches the account balance and holdings.
    """
    client = kis_clients.get(account_no)
    if not client:
        raise HTTPException(status_code=401, detail="Not logged in. Please call /api/v1/auth/login first.")

    try:
        balance_data = client.get_balance()
        return balance_data
    except Exception as e:
        # If the token is expired, the client should handle it.
        # If it fails for other reasons, we return an error.
        raise HTTPException(status_code=500, detail=str(e))
