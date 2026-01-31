from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1 import account, stock
from app.api.v1.endpoints import auth, user_settings
from app.services.stock_master_service import stock_master_service
from app.db.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트 처리"""
    # Startup
    create_db_and_tables()  # DB 초기화
    stock_master_service.initialize()
    yield
    # Shutdown
    # 필요한 정리 작업


app = FastAPI(
    title="KIS API Backend",
    description="한국투자증권 API 백엔드 서비스",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kis-stock-web-ai.vercel.app",
        "http://localhost:3000",  # 로컬 개발용
        "http://localhost:5173",  # Vite 기본 포트
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user_settings.router, prefix="/api/v1", tags=["User Settings"])
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
