from fastapi import FastAPI
from app.api.v1 import auth, account
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="KIS API Backend")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(account.router, prefix="/api/v1/account", tags=["account"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the KIS API Backend"}
