# Issue #4: 종목명/티커 검색 및 주식 현재가 시세 조회 API 구현

**날짜**: 2026-01-24
**이슈 번호**: #4
**상태**: 🔄 In Progress

## 📋 요약

AI 에이전트가 종목명(예: "삼성전자", "Tesla")으로 주식을 검색하고 현재가 시세를 조회할 수 있도록 기능을 구현합니다. KIS API는 종목 코드로만 조회가 가능하므로, 종목명-코드 매핑 시스템과 시세 조회 API를 통합하여 제공합니다.

## 🎯 목표

1. **종목 마스터 데이터 관리** - 종목명-코드 매핑 시스템
2. **현재가 시세 조회 API** - 국내/해외 주식 실시간 시세
3. **통합 검색 엔드포인트** - 종목명 또는 코드로 검색

## 📐 구현 계획

### Phase 1: 요구사항 분석 및 설계

#### 1.1 종목 마스터 데이터 전략

KIS API는 종목 마스터 파일을 직접 제공하지 않으므로, 외부 API를 활용한 하이브리드 방식 선택:

**선택: 하이브리드 캐싱 방식 (옵션 C) ⭐**

**구조:**
1. **데이터 소스**: 네이버 금융 API (비공식)
   - URL: `https://ac.finance.naver.com/ac`
   - 자동완성 API로 실시간 종목 검색 가능

2. **캐싱 전략**:
   - 서버 시작 시 전체 종목 데이터 다운로드
   - 메모리에 캐싱 (딕셔너리 인덱스)
   - 매일 자동 업데이트 (스케줄러)

3. **검색 흐름**:
   ```
   사용자 입력 → 메모리 캐시 검색 (빠름) → 종목코드 반환
   ```

**장점:**
- ✅ 실시간 데이터 (매일 자동 업데이트)
- ✅ 빠른 검색 속도 (메모리 캐시)
- ✅ API 호출 최소화 (하루 1회)
- ✅ 외부 API 장애 시에도 캐시 사용 가능
- ✅ 마스터 파일 수동 관리 불필요

**단점:**
- ⚠️ 비공식 API 사용 (변경 가능성)
- ⚠️ 초기 구현이 약간 복잡

**대안 (Fallback)**:
- 네이버 API 장애 시 → 공공데이터포털 KRX API 사용
- 또는 로컬 백업 JSON 파일 사용

#### 1.2 데이터 소스 및 캐시 구조

**네이버 금융 API (국내 주식)**
- **URL**: `https://ac.finance.naver.com/ac`
- **요청 예시**:
  ```python
  params = {
      "q": "삼성전자",
      "q_enc": "utf-8",
      "st": "111",  # 111: 증권
      "frm": "stock",
      "r_format": "json"
  }
  ```
- **응답 예시**:
  ```json
  {
    "items": [
      ["005930|삼성전자|KODEX 삼성그룹"],
      ["005935|삼성전자우|KODEX 삼성그룹우선주"]
    ]
  }
  ```

**메모리 캐시 구조 (Python 딕셔너리)**
```python
{
  "domestic": {
    "by_code": {
      "005930": {
        "code": "005930",
        "name": "삼성전자",
        "market": "KOSPI"
      }
    },
    "by_name": {
      "삼성전자": "005930",
      "SAMSUNG": "005930"  # 영문명도 지원
    }
  },
  "overseas": {
    "by_symbol": {
      "AAPL": {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASD"
      }
    },
    "by_name": {
      "APPLE": "AAPL",
      "애플": "AAPL"
    }
  },
  "last_updated": "2026-01-24T09:00:00"
}
```

#### 1.3 KIS 현재가 조회 API 분석

**국내 주식 현재가 조회**
- **TR ID (실전):** `FHKST01010100`
- **TR ID (모의):** `FHKST01010100` (동일)
- **URL:** `{base_url}/uapi/domestic-stock/v1/quotations/inquire-price`

**요청 파라미터:**
```python
params = {
    "FID_COND_MRKT_DIV_CODE": "J",  # 시장분류코드 (J:주식)
    "FID_INPUT_ISCD": "005930"       # 종목코드
}
```

**응답 구조:**
```json
{
  "rt_cd": "0",
  "output": {
    "stck_prpr": "75000",      // 현재가
    "prdy_vrss": "1000",       // 전일대비
    "prdy_vrss_sign": "2",     // 전일대비부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
    "prdy_ctrt": "1.35",       // 전일대비율
    "acml_vol": "12345678",    // 누적거래량
    "stck_oprc": "74000",      // 시가
    "stck_hgpr": "76000",      // 고가
    "stck_lwpr": "73500",      // 저가
    "stck_mxpr": "97500",      // 상한가
    "stck_llam": "52500",      // 하한가
    "per": "12.34",            // PER
    "pbr": "1.23",             // PBR
    "eps": "6089",             // EPS
    "bps": "61234"             // BPS
  }
}
```

**해외 주식 현재가 조회**
- **TR ID (실전):** `HHDFS00000300`
- **TR ID (모의):** `HHDFS00000300` (동일)
- **URL:** `{base_url}/uapi/overseas-price/v1/quotations/price`

**요청 파라미터:**
```python
params = {
    "AUTH": "",
    "EXCD": "NAS",    # 거래소코드 (NAS:나스닥, NYS:뉴욕, AMS:아멕스)
    "SYMB": "AAPL"    # 심볼
}
```

**응응 구조:**
```json
{
  "rt_cd": "0",
  "output": {
    "last": "182.50",       // 현재가
    "diff": "2.30",         // 전일대비
    "rate": "1.28",         // 등락률
    "tvol": "52340000",     // 거래량
    "open": "180.20",       // 시가
    "high": "183.00",       // 고가
    "low": "179.80",        // 저가
    "tomv": "9525000000"    // 거래대금
  }
}
```

#### 1.4 API 설계

**엔드포인트:**
```
GET /api/v1/stock/quote?keyword={keyword}
```

**Query Parameters:**
- `keyword` (required): 종목명 또는 종목코드/심볼
  - 예: "삼성전자", "005930", "AAPL", "Apple"

**통합 응답 스키마:**
```json
{
  "market": "DOMESTIC",        // DOMESTIC | OVERSEAS
  "symbol": "005930",          // 종목코드/심볼
  "name": "삼성전자",          // 종목명
  "current_price": "75000",    // 현재가
  "change": "1000",            // 전일대비 (절대값)
  "change_rate": "1.35",       // 등락률 (%)
  "change_direction": "UP",    // UP | DOWN | UNCHANGED
  "volume": "12345678",        // 거래량
  "open": "74000",             // 시가
  "high": "76000",             // 고가
  "low": "73500",              // 저가
  "currency": "KRW",           // KRW | USD
  "updated_at": "2026-01-24T10:30:00"  // 조회 시각
}
```

### Phase 2: 코드 구조 설계

#### 2.1 디렉토리 구조

```
kis_api_backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── account.py       # 기존
│   │       └── stock.py         # 신규: 주식 관련 엔드포인트
│   ├── services/
│   │   ├── token_manager.py     # 기존
│   │   ├── account_service.py   # 기존
│   │   └── stock_service.py     # 신규: 주식 검색 및 시세 조회
│   ├── schemas/
│   │   ├── common.py            # 기존
│   │   ├── holdings.py          # 기존
│   │   └── stock.py             # 신규: 주식 시세 스키마
│   └── data/
│       └── master/              # 신규: 마스터 데이터
│           ├── domestic_stocks.json
│           └── overseas_stocks.json
├── kis_client.py                # 기존 파일 확장
└── tests/
    ├── test_stock_service.py    # 신규
    └── test_stock_api.py        # 신규
```

#### 2.2 클래스 및 함수 설계

**1) `app/schemas/stock.py` - 주식 시세 스키마**
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .common import Currency

class StockQuote(BaseModel):
    """주식 현재가 시세"""
    market: str = Field(..., description="시장 구분 (DOMESTIC/OVERSEAS)")
    symbol: str = Field(..., description="종목코드/심볼")
    name: str = Field(..., description="종목명")
    current_price: str = Field(..., description="현재가")
    change: str = Field(..., description="전일대비")
    change_rate: str = Field(..., description="등락률(%)")
    change_direction: str = Field(..., description="UP/DOWN/UNCHANGED")
    volume: str = Field(..., description="거래량")
    open: str = Field(..., description="시가")
    high: str = Field(..., description="고가")
    low: str = Field(..., description="저가")
    currency: Currency = Field(..., description="통화")
    updated_at: str = Field(..., description="조회 시각")
```

**2) `app/services/stock_service.py` - 주식 검색 및 시세 서비스**
```python
class StockService:
    """주식 검색 및 시세 조회 서비스"""

    def __init__(self, kis_client: KISClient):
        self.kis_client = kis_client
        self.domestic_master = self._load_domestic_master()
        self.overseas_master = self._load_overseas_master()

    def search_stock(self, keyword: str) -> Optional[Dict]:
        """
        종목 검색 (종목명 또는 코드)

        Args:
            keyword: 검색 키워드

        Returns:
            Dict: 종목 정보 (code/symbol, name, market)
        """
        # 1. 국내 주식 검색
        domestic = self._search_domestic(keyword)
        if domestic:
            return domestic

        # 2. 해외 주식 검색
        overseas = self._search_overseas(keyword)
        if overseas:
            return overseas

        return None

    def get_quote(self, keyword: str) -> StockQuote:
        """
        주식 현재가 조회

        Args:
            keyword: 종목명 또는 코드

        Returns:
            StockQuote: 현재가 정보
        """
        # 1. 종목 검색
        stock = self.search_stock(keyword)
        if not stock:
            raise ValueError(f"종목을 찾을 수 없습니다: {keyword}")

        # 2. 시세 조회
        if stock["market"] == "DOMESTIC":
            return self._get_domestic_quote(stock["code"])
        else:
            return self._get_overseas_quote(stock["symbol"], stock["exchange"])

    def _load_domestic_master(self) -> Dict:
        """국내 주식 마스터 데이터 로드"""
        pass

    def _load_overseas_master(self) -> Dict:
        """해외 주식 마스터 데이터 로드"""
        pass

    def _search_domestic(self, keyword: str) -> Optional[Dict]:
        """국내 주식 검색"""
        pass

    def _search_overseas(self, keyword: str) -> Optional[Dict]:
        """해외 주식 검색"""
        pass

    def _get_domestic_quote(self, code: str) -> StockQuote:
        """국내 주식 현재가 조회"""
        pass

    def _get_overseas_quote(self, symbol: str, exchange: str) -> StockQuote:
        """해외 주식 현재가 조회"""
        pass
```

**3) `kis_client.py` - KIS API 클라이언트 확장**
```python
def get_domestic_stock_price(self, stock_code: str) -> Dict[str, Any]:
    """
    국내 주식 현재가 조회

    Args:
        stock_code: 종목코드 (6자리)

    Returns:
        Dict: KIS API 원본 응답
    """
    pass

def get_overseas_stock_price(self, symbol: str, exchange_code: str) -> Dict[str, Any]:
    """
    해외 주식 현재가 조회

    Args:
        symbol: 심볼 (예: AAPL)
        exchange_code: 거래소 코드 (NAS/NYS/AMS)

    Returns:
        Dict: KIS API 원본 응답
    """
    pass
```

**4) `app/api/v1/stock.py` - 주식 API 엔드포인트**
```python
from fastapi import APIRouter, HTTPException, Query
from app.schemas.stock import StockQuote
from app.services.stock_service import StockService

router = APIRouter()

@router.get("/quote", response_model=StockQuote)
def get_stock_quote(
    keyword: str = Query(..., description="종목명 또는 종목코드/심볼")
):
    """
    주식 현재가 조회

    종목명 또는 종목코드/심볼로 주식의 현재가 시세를 조회합니다.

    Args:
        keyword: 검색 키워드
            - 국내: "삼성전자", "005930"
            - 해외: "Apple", "AAPL"

    Returns:
        StockQuote: 현재가 시세 정보
    """
    try:
        stock_service = StockService(kis_client)
        return stock_service.get_quote(keyword)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {str(e)}")
```

### Phase 3: 구현 단계

#### Step 1: 마스터 데이터 준비
1. `app/data/master/` 디렉토리 생성
2. 국내 주식 마스터 데이터 생성 (주요 종목 우선)
3. 해외 주식 마스터 데이터 생성 (주요 미국 주식)

#### Step 2: 스키마 정의
1. `app/schemas/stock.py` 생성 - StockQuote 스키마

#### Step 3: KIS API 클라이언트 확장
1. `get_domestic_stock_price()` 메서드 추가
2. `get_overseas_stock_price()` 메서드 추가

#### Step 4: 서비스 계층 구현
1. `app/services/stock_service.py` 생성
2. 마스터 데이터 로드 및 검색 로직 구현
3. 시세 조회 및 데이터 파싱 구현

#### Step 5: API 엔드포인트 추가
1. `app/api/v1/stock.py` 생성
2. `/quote` 엔드포인트 구현
3. `app/main.py`에 라우터 등록

#### Step 6: 테스트
1. 종목명 검색 테스트 (한글/영문)
2. 종목코드 직접 조회 테스트
3. 존재하지 않는 종목 에러 처리 테스트

## 🔑 핵심 고려사항

### 1. 마스터 데이터 품질
- 초기에는 주요 종목만 포함 (코스피 200, 나스닥 100 등)
- 주기적 업데이트 필요 (신규 상장, 상장폐지)
- 한글 검색 시 완전 일치 또는 부분 일치 전략

### 2. 검색 알고리즘
- 정확도 우선: 완전 일치 → 부분 일치
- 대소문자 구분 없음 (해외 주식)
- 한글/영문 별칭 지원 (예: "삼성전자", "SAMSUNG")

### 3. 시세 데이터 신선도
- KIS API는 실시간 또는 지연 시세 제공
- 모의투자는 실제 시세와 다를 수 있음
- 조회 시각을 응답에 포함

### 4. 성능 최적화
- 마스터 데이터는 메모리에 캐싱
- 검색 시 인덱스 활용 (딕셔너리)
- API 호출 횟수 최소화

## 🧪 테스트 계획

### 1. 단위 테스트
```python
def test_search_domestic_by_name():
    """종목명으로 국내 주식 검색"""
    result = stock_service.search_stock("삼성전자")
    assert result["code"] == "005930"

def test_search_domestic_by_code():
    """종목코드로 국내 주식 검색"""
    result = stock_service.search_stock("005930")
    assert result["name"] == "삼성전자"

def test_search_overseas_by_name():
    """종목명으로 해외 주식 검색"""
    result = stock_service.search_stock("Apple")
    assert result["symbol"] == "AAPL"
```

### 2. 통합 테스트
```python
def test_get_quote_by_name():
    """종목명으로 시세 조회"""
    response = client.get("/api/v1/stock/quote?keyword=삼성전자")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "005930"
    assert "current_price" in data

def test_get_quote_not_found():
    """존재하지 않는 종목"""
    response = client.get("/api/v1/stock/quote?keyword=없는종목")
    assert response.status_code == 404
```

## ✅ 완료 조건 (Acceptance Criteria)

1. ✅ `GET /api/v1/stock/quote?keyword=삼성전자` → 종목코드 005930으로 변환하여 시세 반환
2. ✅ `GET /api/v1/stock/quote?keyword=005930` → 동일한 시세 반환
3. ✅ `GET /api/v1/stock/quote?keyword=AAPL` → 해외 주식 시세 반환
4. ✅ 존재하지 않는 종목 → 404 에러 및 명확한 메시지
5. ✅ 응답 스키마 통일 (국내/해외 구분 없이)
6. ✅ Swagger UI에서 API 문서 확인 가능

## 📊 예상 작업 파일

**신규 파일:**
- `app/api/v1/stock.py` - 주식 관련 엔드포인트
- `app/services/stock_service.py` - 주식 검색 및 시세 서비스
- `app/schemas/stock.py` - 주식 시세 스키마
- `app/data/master/domestic_stocks.json` - 국내 주식 마스터
- `app/data/master/overseas_stocks.json` - 해외 주식 마스터
- `tests/test_stock_service.py` - 단위 테스트
- `tests/test_stock_api.py` - 통합 테스트

**수정 파일:**
- `kis_client.py` - 시세 조회 메서드 추가
- `app/main.py` - 라우터 등록

## 📚 참고 자료

- [KIS API - 국내주식 현재가 시세](https://apiportal.koreainvestment.com/apiservice/apiservice-domestic-stock-quotations)
- [KIS API - 해외주식 현재가](https://apiportal.koreainvestment.com/apiservice/apiservice-overseas-stock-quotations)
- [한국거래소 상장종목 정보](http://data.krx.co.kr)
- FastAPI Query Parameters: https://fastapi.tiangolo.com/tutorial/query-params/

## 🚀 다음 단계

이 이슈가 완료되면:
- 주식 매매 API 구현 (매수/매도 주문)
- 관심종목 관리 기능
- 실시간 시세 WebSocket 연동

---

**작성자**: Claude Code
**마지막 업데이트**: 2026-01-24 (계획 수립)
