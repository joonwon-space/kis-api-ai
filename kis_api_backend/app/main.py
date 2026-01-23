from fastapi import FastAPI
from app.api.v1 import account

app = FastAPI(
    title="KIS API Backend",
    description="한국투자증권 API 백엔드 서비스",
    version="1.0.0"
)

# Include routers
app.include_router(account.router, prefix="/api/v1/account", tags=["account"])


@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "KIS API Backend is running"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
