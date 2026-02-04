"""통계 서비스 테스트"""
import pytest
from datetime import date, timedelta
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from app.db.models import User, DailyAsset
from app.services.asset_snapshot_service import AssetSnapshotService
from app.services.stats_service import StatsService
from app.schemas.dashboard import DashboardSummary


@pytest.fixture(name="session")
def session_fixture():
    """테스트용 인메모리 DB 세션"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """테스트 사용자 생성"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="sample_snapshots")
def sample_snapshots_fixture(session: Session, test_user: User):
    """샘플 스냅샷 데이터 생성"""
    snapshots = []
    base_date = date.today() - timedelta(days=30)

    for i in range(31):
        snapshot_date = base_date + timedelta(days=i)
        snapshot = DailyAsset(
            user_id=test_user.id,
            snapshot_date=snapshot_date,
            total_asset=1000000 + (i * 10000),  # 매일 1만원씩 증가
            total_purchase_amount=1000000,
            total_profit_loss=i * 10000,
            profit_loss_rate=(i * 10000) / 1000000 * 100,
            deposit=100000,
            stock_evaluation=900000 + (i * 10000)
        )
        session.add(snapshot)
        snapshots.append(snapshot)

    session.commit()
    return snapshots


class TestAssetSnapshotService:
    """자산 스냅샷 서비스 테스트"""

    def test_save_snapshot(self, session: Session, test_user: User):
        """스냅샷 저장 테스트"""
        service = AssetSnapshotService(session)
        summary = DashboardSummary(
            total_assets="1500000",
            total_deposit="300000",
            total_profit_loss="200000",
            profit_loss_rate="20.0",
            stock_count=5
        )

        snapshot = service.save_snapshot(test_user.id, summary)

        assert snapshot.id is not None
        assert snapshot.user_id == test_user.id
        assert snapshot.total_asset == 1500000
        assert snapshot.profit_loss_rate == 20.0

    def test_get_snapshot(self, session: Session, test_user: User, sample_snapshots):
        """특정 날짜 스냅샷 조회 테스트"""
        service = AssetSnapshotService(session)
        today = date.today()

        snapshot = service.get_snapshot(test_user.id, today)

        assert snapshot is not None
        assert snapshot.snapshot_date == today

    def test_get_latest_snapshot(self, session: Session, test_user: User, sample_snapshots):
        """최신 스냅샷 조회 테스트"""
        service = AssetSnapshotService(session)

        latest = service.get_latest_snapshot(test_user.id)

        assert latest is not None
        assert latest.snapshot_date == date.today()


class TestStatsService:
    """통계 서비스 테스트"""

    def test_get_daily_stats(self, session: Session, test_user: User, sample_snapshots):
        """일별 통계 조회 테스트"""
        service = StatsService(session)

        daily_stats = service.get_daily_stats(test_user.id, days=30)

        assert len(daily_stats) >= 30  # 최소 30개
        assert daily_stats[0].total_asset >= 1000000
        assert daily_stats[-1].total_asset >= 1290000

    def test_get_monthly_stats(self, session: Session, test_user: User, sample_snapshots):
        """월별 통계 조회 테스트"""
        service = StatsService(session)

        monthly_stats = service.get_monthly_stats(test_user.id, months=1)

        assert len(monthly_stats) >= 1
        if len(monthly_stats) > 0:
            assert monthly_stats[0].start_asset > 0
            assert monthly_stats[0].end_asset > 0

    def test_get_yearly_stats(self, session: Session, test_user: User, sample_snapshots):
        """연도별 통계 조회 테스트"""
        service = StatsService(session)

        yearly_stats = service.get_yearly_stats(test_user.id, years=1)

        assert len(yearly_stats) >= 1
        if len(yearly_stats) > 0:
            assert yearly_stats[0].year == date.today().year
            assert yearly_stats[0].start_asset > 0
