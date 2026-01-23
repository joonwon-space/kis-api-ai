# Issue #2: 국내 및 해외 주식 보유 종목 상세 조회 API 구현

**날짜**: 2026-01-23
**이슈 번호**: #2
**상태**: 🔄 In Progress

## 📋 요약

AI 에이전트가 현재 포트폴리오 상태를 정확하게 분석할 수 있도록, 국내 주식과 해외(미국) 주식의 보유 현황을 종목별로 상세 조회하는 기능을 구현합니다. 기존 이슈 #1의 단순 잔고 조회를 고도화하여, 종목별 수량, 평단가, 수익률, 평가금액 등의 상세 데이터를 제공합니다.

## 🎯 목표

1. **국내 주식 보유 내역 고도화** - 기존 balance API 개선
2. **해외 주식 잔고 조회 기능 추가** - 미국 주식 지원
3. **통합 포트폴리오 API 구현** - 국내/해외/전체 선택 조회

## 📐 구현 계획

### Phase 1: KIS API 분석 및 설계

#### 1.1 국내 주식 잔고 조회 API 분석

**KIS API 엔드포인트:**
- **TR ID (실전):** `TTTC8434R` - 주식잔고조회
- **TR ID (모의):** `VTTC8434R`
- **URL:** `{base_url}/uapi/domestic-stock/v1/trading/inquire-balance`

**요청 파라미터:**
```python
params = {
    "CANO": "계좌번호",
    "ACNT_PRDT_CD": "계좌상품코드",
    "AFHR_FLPR_YN": "N",      # 시간외단일가여부
    "OFL_YN": "",              # 오프라인여부
    "INQR_DVSN": "02",         # 조회구분 (01:대출일별, 02:종목별)
    "UNPR_DVSN": "01",         # 단가구분
    "FUND_STTL_ICLD_YN": "N",  # 펀드결제분포함여부
    "FNCG_AMT_AUTO_RDPT_YN": "N",  # 융자금액자동상환여부
    "PRCS_DVSN": "00",         # 처리구분 (00:전일매매포함, 01:전일매매미포함)
    "CTX_AREA_FK100": "",      # 연속조회검색조건
    "CTX_AREA_NK100": ""       # 연속조회키
}
```

**응답 구조:**
```json
{
  "rt_cd": "0",
  "msg_cd": "정상",
  "output1": [  // 보유 종목 리스트
    {
      "pdno": "005930",           // 종목코드
      "prdt_name": "삼성전자",    // 종목명
      "hldg_qty": "10",           // 보유수량
      "pchs_avg_pric": "70000",   // 매입평균가격
      "prpr": "75000",            // 현재가
      "evlu_amt": "750000",       // 평가금액
      "evlu_pfls_amt": "50000",   // 평가손익금액
      "evlu_pfls_rt": "7.14"      // 평가손익율
    }
  ],
  "output2": {  // 계좌 요약 정보
    "tot_evlu_amt": "10000000",   // 총평가금액
    "pchs_amt_smtl_amt": "9500000", // 매입금액합계
    "evlu_pfls_smtl_amt": "500000", // 평가손익합계
    "evlu_pfls_rt": "5.26",         // 평가손익율
    "dnca_tot_amt": "5000000"       // 예수금총액
  }
}
```

**페이징 처리:**
- 보유 종목이 많을 경우 `CTX_AREA_FK100`, `CTX_AREA_NK100`를 사용하여 연속 조회
- 첫 응답의 `ctx_area_fk100`, `ctx_area_nk100` 값을 다음 요청에 전달

#### 1.2 해외 주식 잔고 조회 API 분석

**KIS API 엔드포인트:**
- **TR ID (실전):** `TTTS3012R` - 해외주식 잔고
- **TR ID (모의):** `JTTT3012R`
- **URL:** `{base_url}/uapi/overseas-stock/v1/trading/inquire-balance`

**요청 파라미터:**
```python
params = {
    "CANO": "계좌번호",
    "ACNT_PRDT_CD": "계좌상품코드",
    "OVRS_EXCG_CD": "NASD",    # 해외거래소코드 (NASD:나스닥, NYSE:뉴욕, AMEX:아멕스)
    "TR_CRCY_CD": "USD",        # 거래통화코드
    "CTX_AREA_FK200": "",       # 연속조회검색조건
    "CTX_AREA_NK200": ""        # 연속조회키
}
```

**응답 구조:**
```json
{
  "rt_cd": "0",
  "msg_cd": "정상",
  "output1": [  // 보유 종목 리스트
    {
      "ovrs_pdno": "TSLA",           // 해외종목코드
      "ovrs_item_name": "TESLA INC", // 종목명
      "frcr_pchs_amt1": "200.50",    // 외화매입금액
      "ovrs_cblc_qty": "10",         // 해외잔고수량
      "now_pric2": "250.75",         // 현재가
      "ovrs_stck_evlu_amt": "2507.50", // 해외주식평가금액
      "frcr_evlu_pfls_amt": "102.50",  // 외화평가손익금액
      "evlu_pfls_rt": "5.12"           // 평가손익율
    }
  ],
  "output2": {  // 계좌 요약
    "frcr_pchs_amt1": "1000.00",     // 외화매입금액
    "ovrs_tot_pfls": "50.00",         // 해외총손익
    "tot_evlu_pfls_amt": "1050.00"    // 총평가손익금액
  }
}
```

**환율 처리:**
- 응답 데이터는 USD 기준
- 원화 환산은 별도 환율 API 또는 고정 환율 사용 검토
- 우선은 USD 데이터만 제공하고, 향후 환율 변환 기능 추가 고려

#### 1.3 API 설계: 통합 포트폴리오 조회

**새로운 엔드포인트:**
```
GET /api/v1/account/holdings
```

**Query Parameter:**
- `market_type` (optional, default: `ALL`)
  - `ALL`: 국내 + 해외 합산
  - `DOMESTIC`: 국내 주식만
  - `OVERSEAS`: 해외 주식만

**통합 응답 스키마:**
```json
{
  "market_type": "ALL",
  "summary": {
    "total_evaluation": 15000000,     // 총 평가금액 (원화)
    "total_purchase": 14000000,        // 총 매입금액 (원화)
    "total_profit_loss": 1000000,      // 총 손익 (원화)
    "profit_loss_rate": 7.14           // 총 수익률
  },
  "holdings": [
    {
      "market": "DOMESTIC",            // 시장 구분
      "symbol": "005930",              // 종목코드
      "name": "삼성전자",              // 종목명
      "quantity": "10",                // 보유수량
      "avg_price": "70000",            // 매입평균가 (원화)
      "current_price": "75000",        // 현재가 (원화)
      "evaluation_amount": "750000",   // 평가금액 (원화)
      "profit_loss": "50000",          // 손익금액 (원화)
      "profit_loss_rate": "7.14",      // 수익률 (%)
      "currency": "KRW"                // 통화
    },
    {
      "market": "OVERSEAS",
      "symbol": "TSLA",
      "name": "TESLA INC",
      "quantity": "10",
      "avg_price": "200.50",           // 매입평균가 (USD)
      "current_price": "250.75",       // 현재가 (USD)
      "evaluation_amount": "2507.50",  // 평가금액 (USD)
      "profit_loss": "502.50",         // 손익금액 (USD)
      "profit_loss_rate": "5.12",      // 수익률 (%)
      "currency": "USD"                // 통화
    }
  ]
}
```

### Phase 2: 코드 구조 설계

#### 2.1 디렉토리 구조

```
kis_api_backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── account.py           # 엔드포인트 (기존 파일 수정)
│   ├── services/
│   │   ├── token_manager.py         # 기존
│   │   └── account_service.py       # 신규: 비즈니스 로직 분리
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── holdings.py              # 신규: 보유종목 스키마
│   │   └── common.py                # 신규: 공통 스키마 (MarketType enum 등)
│   └── core/
│       └── exceptions.py            # 신규: 커스텀 예외
├── kis_client.py                    # 기존 파일 확장
└── tests/
    ├── test_account_service.py      # 신규
    └── test_holdings_api.py         # 신규
```

#### 2.2 클래스 및 함수 설계

**1) `app/schemas/common.py` - 공통 스키마**
```python
from enum import Enum
from pydantic import BaseModel

class MarketType(str, Enum):
    ALL = "ALL"
    DOMESTIC = "DOMESTIC"
    OVERSEAS = "OVERSEAS"

class Currency(str, Enum):
    KRW = "KRW"
    USD = "USD"
```

**2) `app/schemas/holdings.py` - 보유종목 스키마**
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from .common import MarketType, Currency

class HoldingItem(BaseModel):
    """개별 보유 종목"""
    market: str = Field(..., description="시장 구분 (DOMESTIC/OVERSEAS)")
    symbol: str = Field(..., description="종목코드")
    name: str = Field(..., description="종목명")
    quantity: str = Field(..., description="보유수량")
    avg_price: str = Field(..., description="매입평균가")
    current_price: str = Field(..., description="현재가")
    evaluation_amount: str = Field(..., description="평가금액")
    profit_loss: str = Field(..., description="손익금액")
    profit_loss_rate: str = Field(..., description="수익률(%)")
    currency: Currency = Field(..., description="통화")

class HoldingsSummary(BaseModel):
    """보유 종목 요약"""
    total_evaluation: Optional[str] = Field(None, description="총 평가금액")
    total_purchase: Optional[str] = Field(None, description="총 매입금액")
    total_profit_loss: Optional[str] = Field(None, description="총 손익")
    profit_loss_rate: Optional[str] = Field(None, description="총 수익률(%)")

class HoldingsResponse(BaseModel):
    """보유 종목 조회 응답"""
    market_type: MarketType
    summary: HoldingsSummary
    holdings: List[HoldingItem]
```

**3) `kis_client.py` - KIS API 클라이언트 확장**

기존 `KISClient` 클래스에 다음 메서드 추가:
```python
def get_domestic_holdings(self) -> Dict[str, Any]:
    """
    국내 주식 보유 내역 조회 (상세)

    Returns:
        Dict: KIS API 원본 응답 (output1, output2 포함)
    """
    pass

def get_overseas_holdings(self, exchange_code: str = "NASD") -> Dict[str, Any]:
    """
    해외 주식 보유 내역 조회

    Args:
        exchange_code: 거래소 코드 (NASD, NYSE, AMEX)

    Returns:
        Dict: KIS API 원본 응답
    """
    pass
```

**4) `app/services/account_service.py` - 비즈니스 로직**

```python
from typing import List
from app.schemas.holdings import HoldingsResponse, HoldingItem, HoldingsSummary
from app.schemas.common import MarketType, Currency
from kis_client import KISClient

class AccountService:
    """계좌 관련 비즈니스 로직"""

    def __init__(self, kis_client: KISClient):
        self.kis_client = kis_client

    def get_holdings(self, market_type: MarketType = MarketType.ALL) -> HoldingsResponse:
        """
        보유 종목 조회 (통합)

        Args:
            market_type: 시장 구분 (ALL/DOMESTIC/OVERSEAS)

        Returns:
            HoldingsResponse: 통합 포트폴리오 데이터
        """
        holdings = []

        if market_type in [MarketType.ALL, MarketType.DOMESTIC]:
            domestic_data = self.kis_client.get_domestic_holdings()
            holdings.extend(self._parse_domestic_holdings(domestic_data))

        if market_type in [MarketType.ALL, MarketType.OVERSEAS]:
            overseas_data = self.kis_client.get_overseas_holdings()
            holdings.extend(self._parse_overseas_holdings(overseas_data))

        summary = self._calculate_summary(holdings, market_type)

        return HoldingsResponse(
            market_type=market_type,
            summary=summary,
            holdings=holdings
        )

    def _parse_domestic_holdings(self, data: Dict) -> List[HoldingItem]:
        """국내 주식 데이터 파싱"""
        pass

    def _parse_overseas_holdings(self, data: Dict) -> List[HoldingItem]:
        """해외 주식 데이터 파싱"""
        pass

    def _calculate_summary(self, holdings: List[HoldingItem], market_type: MarketType) -> HoldingsSummary:
        """보유 종목 요약 계산"""
        pass
```

**5) `app/api/v1/account.py` - 엔드포인트 추가**

기존 파일에 새로운 엔드포인트 추가:
```python
from app.schemas.holdings import HoldingsResponse
from app.schemas.common import MarketType
from app.services.account_service import AccountService

@router.get("/holdings", response_model=HoldingsResponse)
def get_holdings(market_type: MarketType = MarketType.ALL):
    """
    보유 종목 조회

    Args:
        market_type: 시장 구분 (ALL/DOMESTIC/OVERSEAS)

    Returns:
        HoldingsResponse: 종목별 상세 정보
    """
    try:
        account_service = AccountService(kis_client)
        return account_service.get_holdings(market_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch holdings: {str(e)}")
```

### Phase 3: 구현 단계

#### Step 1: 스키마 정의
1. `app/schemas/common.py` 생성 - MarketType, Currency enum
2. `app/schemas/holdings.py` 생성 - HoldingItem, HoldingsResponse

#### Step 2: KIS API 클라이언트 확장
1. `kis_client.py`에 `get_domestic_holdings()` 메서드 추가
2. `kis_client.py`에 `get_overseas_holdings()` 메서드 추가
3. 페이징 로직 구현 (선택적)

#### Step 3: 서비스 계층 구현
1. `app/services/account_service.py` 생성
2. `get_holdings()` 메서드 구현
3. 데이터 파싱 로직 구현 (`_parse_domestic_holdings`, `_parse_overseas_holdings`)
4. 요약 계산 로직 구현 (`_calculate_summary`)

#### Step 4: API 엔드포인트 추가
1. `app/api/v1/account.py`에 `/holdings` 엔드포인트 추가
2. 기존 `/balance` 엔드포인트는 유지 (하위 호환성)

#### Step 5: 에러 핸들링 강화
1. `app/core/exceptions.py` 생성 - 커스텀 예외 정의
2. KIS API 에러 코드별 처리 로직 추가

#### Step 6: 테스트
1. Mock을 사용한 단위 테스트 작성
2. 모의투자 계좌로 통합 테스트

## 🔑 핵심 고려사항

### 1. 데이터 일관성
- 국내/해외 주식의 응답 필드명이 다름
- 통일된 스키마로 변환하여 AI가 처리하기 쉽게 설계
- 문자열 타입 유지 (KIS API는 숫자를 문자열로 반환)

### 2. 환율 처리
- 초기 버전: USD 금액 그대로 반환 (currency 필드로 구분)
- 향후: 실시간 환율 API 연동 고려

### 3. 페이징 처리
- 보유 종목이 많을 경우 연속 조회 필요
- 초기 버전: 1회 조회로 제한 (대부분의 개인 투자자는 충분)
- 향후: 재귀 호출로 전체 데이터 수집

### 4. 성능 최적화
- 국내/해외 동시 조회 시 병렬 처리 고려
- 현재는 순차 호출 (간단한 구현 우선)

### 5. 하위 호환성
- 기존 `/balance` 엔드포인트는 유지
- 새로운 `/holdings` 엔드포인트 추가

## 🧪 테스트 계획

### 1. 단위 테스트
```python
# tests/test_account_service.py
def test_parse_domestic_holdings():
    """국내 주식 데이터 파싱 테스트"""
    pass

def test_parse_overseas_holdings():
    """해외 주식 데이터 파싱 테스트"""
    pass

def test_calculate_summary():
    """요약 계산 테스트"""
    pass
```

### 2. 통합 테스트
```python
# tests/test_holdings_api.py
def test_get_holdings_domestic():
    """국내 주식만 조회"""
    response = client.get("/api/v1/account/holdings?market_type=DOMESTIC")
    assert response.status_code == 200
    assert response.json()["market_type"] == "DOMESTIC"

def test_get_holdings_overseas():
    """해외 주식만 조회"""
    response = client.get("/api/v1/account/holdings?market_type=OVERSEAS")
    assert response.status_code == 200
    assert response.json()["market_type"] == "OVERSEAS"

def test_get_holdings_all():
    """전체 조회"""
    response = client.get("/api/v1/account/holdings?market_type=ALL")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "holdings" in data
```

### 3. 수동 테스트
- 모의투자 계좌에서 국내 주식 매수 후 조회
- 모의투자 계좌에서 해외 주식 매수 후 조회
- 빈 포트폴리오일 때 빈 리스트 반환 확인

## ✅ 완료 조건 (Acceptance Criteria)

1. ✅ `GET /api/v1/account/holdings?market_type=OVERSEAS` 호출 시 미국 주식 리스트 반환
2. ✅ 국내/해외 주식의 수익률이 소수점 단위까지 정확하게 계산됨
3. ✅ 보유 종목이 없을 경우 빈 리스트(`[]`) 반환 (에러 없음)
4. ✅ `market_type` 파라미터로 국내/해외/전체 선택 조회 가능
5. ✅ 응답 스키마가 국내/해외 구분 없이 통일됨
6. ✅ 기존 `/balance` 엔드포인트 정상 작동 (하위 호환성)

## 📊 예상 작업 파일

**신규 파일:**
- `app/schemas/__init__.py`
- `app/schemas/common.py`
- `app/schemas/holdings.py`
- `app/services/account_service.py`
- `app/core/__init__.py`
- `app/core/exceptions.py`
- `tests/test_account_service.py`
- `tests/test_holdings_api.py`

**수정 파일:**
- `kis_client.py` - 메서드 추가
- `app/api/v1/account.py` - 엔드포인트 추가

## 📚 참고 자료

- [KIS API - 국내주식잔고조회](https://apiportal.koreainvestment.com/apiservice/apiservice-domestic-stock#L_aade4c72-5fb7-418a-9ff2-254b4d5f0ceb)
- [KIS API - 해외주식잔고조회](https://apiportal.koreainvestment.com/apiservice/apiservice-overseas-stock#L_02672e81-22f3-466d-8d48-8422204c9952)
- FastAPI Response Model: https://fastapi.tiangolo.com/tutorial/response-model/
- Pydantic Enums: https://docs.pydantic.dev/latest/usage/types/#enums-and-choices

## 🚀 다음 단계

이 이슈가 완료되면:
- 주식 매매 API 구현 (매수/매도)
- 실시간 시세 조회 API
- 환율 변환 기능 추가

---

**작성자**: Claude Code
**마지막 업데이트**: 2026-01-23 (계획 수립)
