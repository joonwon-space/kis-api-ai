from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///./kis_api.db"

# SQLite 설정 (개발용)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def create_db_and_tables():
    """DB 및 테이블 초기화"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """DB 세션 의존성"""
    with Session(engine) as session:
        yield session
