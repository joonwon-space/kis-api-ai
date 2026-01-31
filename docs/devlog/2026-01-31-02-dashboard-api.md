# 2026-01-31-02: 통합 대시보드 API - 사용자별 잔고 및 보유종목 조회

**작성일:** 2026-01-31
**관련 Issue:** #12
**작업자:** Claude Code

---

## 📋 작업 개요

### 목적
로그인한 사용자의 저장된 API 키를 복호화하여 KIS API를 호출하고, **총 자산, 예수금, 보유 종목 리스트**를 한 번에 볼 수 있는 대시보드 데이터를 제공합니다.

### 현재 상황 분석
**문제점:**
- `app/api/v1/account.py`에서 글로벌 KIS Client를 사용 (라인 17-23)
- 모든 사용자가 같은 환경변수 기반 계좌 정보를 공유
- 사용자별로 등록한 API 키를 활용하지 못함

**이미 구현된 부분:**
- ✅ KIS Client는 이미 생성자 매개변수로 키를 받도록 설계됨
- ✅ AccountService는 KIS Client를 주입받는 구조
- ✅ UserKey 암호화 저장 및 복호화 기능 (#11)

**필요한 변경:**
1. `app/core/deps.py`에 `get_kis_client` 의존성 추가
2. 기존 엔드포인트들을 사용자별 KIS Client 사용하도록 수정
3. 대시보드 전용 엔드포인트 추가 (요약 정보)

---

## 🎯 요구사항 분석

### 기능 요구사항
1. **사용자별 KIS Client 주입**
   - 로그인한 사용자의 UserKey 조회
   - 복호화 후 KIS Client 동적 생성
   - 키가 없으면 400 에러 반환

2. **대시보드 API**
   - `GET /api/v1/dashboard/summary`: 총 자산, 예수금, 손익 요약
   - `GET /api/v1/dashboard/holdings`: 보유 종목 리스트

3. **기존 엔드포인트 리팩토링**
   - `/api/v1/account/balance` → 사용자별 KIS Client 사용
   - `/api/v1/account/holdings` → 사용자별 KIS Client 사용

### 완료 조건
- [ ] JWT 인증된 사용자가 자신의 계좌 정보를 조회할 수 있음
- [ ] API 키가 없는 사용자는 명확한 에러 메시지 수신
- [ ] 기존 테스트가 깨지지 않고 통과
- [ ] 새로운 대시보드 엔드포인트 테스트 추가

---

## 📐 설계 및 구현 계획

### 1단계: KIS Client 의존성 주입 구현
**파일:** `app/core/deps.py`

```python
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from app.db.database import get_session
from app.db.models import User
from app.services.user_key_service import UserKeyService
from kis_client import KISClient


def get_kis_client(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> KISClient:
    """현재 사용자의 KIS 클라이언트 반환

    사용자의 등록된 API 키를 복호화하여 KIS Client를 동적으로 생성합니다.

    Args:
        current_user: 현재 로그인한 사용자
        session: DB 세션

    Returns:
        KISClient: 사용자별 KIS API 클라이언트

    Raises:
        HTTPException: API 키가 등록되지 않은 경우 400 에러
    """
    service = UserKeyService(session)
    keys = service.get_decrypted_keys(current_user.id)

    if not keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="증권사 API 키가 등록되지 않았습니다. POST /api/v1/user/settings 에서 먼저 등록하세요."
        )

    # 사용자별 KIS Client 생성
    from app.config import settings
    return KISClient(
        app_key=keys.app_key,
        app_secret=keys.app_secret,
        account_no=keys.account_no,
        acnt_prdt_cd=keys.acnt_prdt_cd,
        is_simulation=settings.is_simulation  # 환경 설정은 공유
    )
```

**주요 결정:**
- `get_current_user`를 먼저 호출하여 인증 확인
- 키가 없으면 400 에러 (404가 아님 - 리소스는 있지만 설정 필요)
- `is_simulation`은 환경변수 공유 (서버 전체 설정)

---

### 2단계: Dashboard 스키마 추가
**파일:** `app/schemas/dashboard.py`

```python
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.holdings import HoldingItem


class DashboardSummary(BaseModel):
    """대시보드 요약 정보"""
    total_assets: str = Field(..., description="총 자산 평가액")
    total_deposit: str = Field(..., description="예수금 (현금)")
    total_profit_loss: str = Field(..., description="총 손익")
    profit_loss_rate: Optional[str] = Field(None, description="수익률 (%)")
    stock_count: int = Field(..., description="보유 종목 수")

    class Config:
        from_attributes = True


class DashboardHoldingsResponse(BaseModel):
    """대시보드 보유 종목 응답"""
    summary: DashboardSummary
    holdings: List[HoldingItem]

    class Config:
        from_attributes = True
```

**주요 결정:**
- 기존 `HoldingItem` 재사용
- 요약 정보만 별도로 정의

---

### 3단계: Dashboard Service 구현
**파일:** `app/services/dashboard_service.py`

```python
from typing import Dict, Any
from kis_client import KISClient
from app.schemas.dashboard import DashboardSummary, DashboardHoldingsResponse
from app.schemas.holdings import HoldingItem


class DashboardService:
    """대시보드 데이터 제공 서비스"""

    def __init__(self, kis_client: KISClient):
        self.kis_client = kis_client

    def get_summary(self) -> DashboardSummary:
        """대시보드 요약 정보 조회

        Returns:
            DashboardSummary: 총 자산, 예수금, 손익 등
        """
        # KIS API 잔고 조회 (TTTC8434R)
        balance_data = self.kis_client.get_balance()

        # output2에서 요약 정보 추출
        output2 = balance_data.get("output2", {})
        if isinstance(output2, list) and len(output2) > 0:
            output2 = output2[0]

        # output1에서 종목 수 계산
        output1 = balance_data.get("output1", [])
        stock_count = len([item for item in output1 if item.get("hldg_qty", "0") != "0"])

        total_assets = output2.get("tot_evlu_amt", "0")
        total_deposit = output2.get("dnca_tot_amt", "0")
        total_profit_loss = output2.get("evlu_pfls_smtl_amt", "0")

        # 수익률 계산
        profit_loss_rate = None
        if total_assets and total_profit_loss:
            try:
                assets = float(total_assets)
                profit = float(total_profit_loss)
                purchase = assets - profit
                if purchase > 0:
                    profit_loss_rate = str(round((profit / purchase) * 100, 2))
            except (ValueError, ZeroDivisionError):
                pass

        return DashboardSummary(
            total_assets=total_assets,
            total_deposit=total_deposit,
            total_profit_loss=total_profit_loss,
            profit_loss_rate=profit_loss_rate,
            stock_count=stock_count
        )

    def get_holdings_with_summary(self) -> DashboardHoldingsResponse:
        """보유 종목 + 요약 정보 조회

        Returns:
            DashboardHoldingsResponse: 요약 + 종목 리스트
        """
        balance_data = self.kis_client.get_balance()
        summary = self.get_summary()

        # 보유 종목 파싱
        output1 = balance_data.get("output1", [])
        holdings = []

        for item in output1:
            quantity = item.get("hldg_qty", "0")
            if quantity == "0":
                continue

            holding = HoldingItem(
                market="DOMESTIC",
                symbol=item.get("pdno", ""),
                name=item.get("prdt_name", ""),
                quantity=quantity,
                avg_price=item.get("pchs_avg_pric", "0"),
                current_price=item.get("prpr", "0"),
                evaluation_amount=item.get("evlu_amt", "0"),
                profit_loss=item.get("evlu_pfls_amt", "0"),
                profit_loss_rate=item.get("evlu_pfls_rt", "0"),
                currency="KRW"
            )
            holdings.append(holding)

        return DashboardHoldingsResponse(
            summary=summary,
            holdings=holdings
        )
```

**주요 결정:**
- KIS API의 `get_balance()` 응답 재사용
- `output2`에서 요약, `output1`에서 종목 리스트 추출
- 일단 국내 주식만 지원 (해외는 별도 API 필요)

---

### 4단계: Dashboard API 엔드포인트 추가
**파일:** `app/api/v1/endpoints/dashboard.py`

```python
from fastapi import APIRouter, Depends
from kis_client import KISClient
from app.core.deps import get_current_user, get_kis_client
from app.db.models import User
from app.schemas.dashboard import DashboardSummary, DashboardHoldingsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    kis_client: KISClient = Depends(get_kis_client)
):
    """대시보드 요약 정보 조회

    로그인한 사용자의 증권 계좌 요약 정보를 제공합니다.

    Args:
        current_user: 현재 로그인한 사용자
        kis_client: 사용자별 KIS API 클라이언트

    Returns:
        DashboardSummary: 총 자산, 예수금, 손익, 보유 종목 수
    """
    service = DashboardService(kis_client)
    return service.get_summary()


@router.get("/holdings", response_model=DashboardHoldingsResponse)
def get_dashboard_holdings(
    current_user: User = Depends(get_current_user),
    kis_client: KISClient = Depends(get_kis_client)
):
    """대시보드 보유 종목 조회

    요약 정보와 함께 보유 종목 상세 리스트를 제공합니다.

    Args:
        current_user: 현재 로그인한 사용자
        kis_client: 사용자별 KIS API 클라이언트

    Returns:
        DashboardHoldingsResponse: 요약 + 종목 리스트
    """
    service = DashboardService(kis_client)
    return service.get_holdings_with_summary()
```

**엔드포인트 등록:**
- `app/main.py`에 라우터 추가

---

### 5단계: 기존 Account 엔드포인트 리팩토링
**파일:** `app/api/v1/account.py`

**Before:**
```python
# 글로벌 KIS Client 초기화
kis_client = KISClient(
    app_key=settings.app_key,
    app_secret=settings.app_secret,
    ...
)

@router.get("/balance")
def get_balance():
    balance_data = kis_client.get_balance()
    ...
```

**After:**
```python
from app.core.deps import get_current_user, get_kis_client

@router.get("/balance")
def get_balance(
    current_user: User = Depends(get_current_user),
    kis_client: KISClient = Depends(get_kis_client)
):
    """계좌 잔고 조회 (사용자별)"""
    balance_data = kis_client.get_balance()
    return balance_data
```

**주요 변경:**
- 글로벌 `kis_client` 제거
- 의존성 주입으로 사용자별 클라이언트 사용
- 기존 로직은 그대로 유지

---

## 🧪 테스트 전략

### 단위 테스트
**파일:** `tests/test_dashboard_service.py`
```python
def test_get_summary(mock_kis_client):
    """요약 정보 조회 테스트"""
    service = DashboardService(mock_kis_client)
    summary = service.get_summary()

    assert summary.total_assets is not None
    assert summary.stock_count >= 0

def test_get_holdings_with_summary(mock_kis_client):
    """보유 종목 + 요약 조회 테스트"""
    service = DashboardService(mock_kis_client)
    response = service.get_holdings_with_summary()

    assert response.summary is not None
    assert isinstance(response.holdings, list)
```

### 통합 테스트
**파일:** `tests/test_api/test_dashboard.py`
```python
def test_dashboard_summary_without_api_key(client, auth_token):
    """API 키 없이 요약 조회 시 400 에러"""
    response = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 400
    assert "API 키가 등록되지 않았습니다" in response.json()["detail"]

def test_dashboard_summary_with_api_key(client, auth_token, user_with_keys):
    """API 키 있을 때 요약 조회 성공"""
    response = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_assets" in data
    assert "stock_count" in data
```

---

## 🔄 Migration 및 배포 계획

### 단계적 적용
1. **Phase 1 (이번 PR):**
   - `get_kis_client` 의존성 추가
   - Dashboard 엔드포인트 신규 추가
   - 기존 account 엔드포인트는 유지 (하위 호환성)

2. **Phase 2 (다음 PR):**
   - 기존 account 엔드포인트를 사용자별 클라이언트로 변경
   - 환경변수 기반 글로벌 클라이언트 제거

3. **Phase 3:**
   - 프론트엔드 연동 테스트
   - 모니터링 및 에러 핸들링 강화

### 하위 호환성
- 기존 `/api/v1/account/*` 엔드포인트는 일단 유지
- 새로운 `/api/v1/dashboard/*` 추가
- 점진적으로 마이그레이션

---

## 📝 구현 파일 목록

### 신규 생성
- `app/schemas/dashboard.py` - Dashboard 스키마
- `app/services/dashboard_service.py` - Dashboard 비즈니스 로직
- `app/api/v1/endpoints/dashboard.py` - Dashboard 엔드포인트
- `tests/test_dashboard_service.py` - 서비스 테스트
- `tests/test_api/test_dashboard.py` - API 테스트

### 수정
- `app/core/deps.py` - `get_kis_client` 의존성 추가
- `app/main.py` - Dashboard 라우터 등록
- (Optional) `app/api/v1/account.py` - 사용자별 클라이언트 사용

---

## 🎯 완료 후 검증

```bash
# 1. 테스트 실행
pytest tests/test_dashboard_service.py -v
pytest tests/test_api/test_dashboard.py -v

# 2. 서버 실행 및 수동 테스트
uvicorn app.main:app --reload

# 3. API 호출 테스트
# 회원가입 & 로그인
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login ...)

# API 키 등록
curl -X POST http://localhost:8000/api/v1/user/settings ...

# 대시보드 요약 조회
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/dashboard/summary

# 보유 종목 조회
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/dashboard/holdings
```

---

**다음 단계:**
- 사용자 승인 후 feature 브랜치 생성
- 단계별 구현 및 커밋
- pytest 테스트 작성 및 검증
- PR 생성 및 리뷰

**예상 커밋 순서:**
1. `feat: KIS Client 의존성 주입 구현 (get_kis_client)`
2. `feat: Dashboard 스키마 및 서비스 구현`
3. `feat: Dashboard API 엔드포인트 추가`
4. `test: Dashboard 기능 테스트 추가`
5. `refactor: Account 엔드포인트 사용자별 클라이언트 적용 (Optional)`
