from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
from app.api.v1 import account, stock
from app.api.v1.endpoints import auth, user_settings, dashboard, stats
from app.services.stock_master_service import stock_master_service
from app.db.firestore import get_firestore_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트 처리"""
    # Startup
    # Firestore 클라이언트 초기화 (싱글톤 생성)
    try:
        get_firestore_client()
        logger.info("Firestore client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Firestore: {e}")
        raise

    # 종목 마스터 데이터를 백그라운드 태스크로 초기화
    # 서버 시작을 블로킹하지 않고, 백그라운드에서 데이터 로드
    asyncio.create_task(stock_master_service.initialize())

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
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["Statistics"])
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
