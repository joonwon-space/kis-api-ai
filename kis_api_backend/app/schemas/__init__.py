from pydantic import BaseModel
from typing import List, Optional

class LoginRequest(BaseModel):
    app_key: Optional[str] = None
    app_secret: Optional[str] = None
    account_no: Optional[str] = None
    acnt_prdt_cd: Optional[str] = None
    is_simulation: bool = True

class Holding(BaseModel):
    name: Optional[str]
    current_price: Optional[str]
    quantity: Optional[str]
    profit_loss_rate: Optional[str]

class BalanceResponse(BaseModel):
    total_asset: Optional[str]
    deposit: Optional[str]
    profit_loss: Optional[str]
    holdings: List[Holding]

class AuthResponse(BaseModel):
    message: str
