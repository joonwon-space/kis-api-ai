from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1 import account, stock
from app.services.stock_master_service import stock_master_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트 처리"""
    # Startup
    await stock_master_service.initialize()
    yield
    # Shutdown
    # 필요한 정리 작업


app = FastAPI(
    title="KIS API Backend",
    description="한국투자증권 API 백엔드 서비스",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(account.router, prefix="/api/v1/account", tags=["account"])
app.include_router(stock.router, prefix="/api/v1/stock", tags=["stock"])


@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "KIS API Backend is running"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
