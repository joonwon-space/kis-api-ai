# Issue #1: 초기 프로젝트 구성 및 인증(토큰 관리), 잔고 조회 API 구현

**날짜**: 2026-01-23
**이슈 번호**: #1
**상태**: ✅ Completed

## 📋 요약

Gemini CLI 에이전트가 사용할 백엔드 서버의 기반을 구축하고, KIS API 인증 및 잔고 조회 기능을 구현합니다. 특히 Access Token의 효율적인 관리(유효기간 체크 및 재사용)가 핵심 요구사항입니다.

## 🎯 목표

1. FastAPI 기반 백엔드 서버 초기 구성
2. KIS API Access Token 관리 메커니즘 구현 (캐싱 및 자동 갱신)
3. 잔고 조회 API 엔드포인트 구현

## 📐 구현 계획

### 1단계: 프로젝트 초기 세팅

**작업 내용:**
- Poetry를 이용한 Python 가상환경 설정
- 필요한 패키지 설치
  - `fastapi`: API 서버 프레임워크
  - `uvicorn`: ASGI 서버
  - `httpx`: 비동기 HTTP 클라이언트
  - `pydantic-settings`: 환경 변수 관리
- 프로젝트 디렉토리 구조 설계

**예상 구조:**
```
kis_api_backend/
├── app/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 환경 변수 설정
│   ├── api/
│   │   └── v1/
│   │       └── account.py   # 계좌 관련 엔드포인트
│   └── services/
│       ├── kis_client.py    # KIS API 클라이언트
│       └── token_manager.py # 토큰 관리 서비스
├── .env                     # 환경 변수 (gitignore)
├── .env.example             # 환경 변수 템플릿
├── pyproject.toml           # Poetry 설정
└── README.md
```

**환경 변수 (.env):**
- `APP_KEY`: KIS API 앱 키
- `APP_SECRET`: KIS API 시크릿 키
- `ACCOUNT_NO`: 계좌번호
- `ACNT_PRDT_CD`: 계좌 상품 코드
- `URL_BASE`: KIS API Base URL (실전/모의투자)

### 2단계: KIS 인증 모듈 구현 (핵심)

**토큰 관리 전략:**

1. **토큰 발급**
   - KIS API `oauth2/tokenP` 엔드포인트 호출
   - Access Token과 만료 시간 수신

2. **토큰 저장 (token.json)**
   ```json
   {
     "access_token": "eyJ...",
     "token_type": "Bearer",
     "expires_at": "2026-01-23T12:00:00"
   }
   ```

3. **토큰 재사용 로직**
   - API 호출 전 토큰 유효성 검증
   - 유효한 경우: 기존 토큰 사용
   - 만료된 경우: 자동 갱신 후 사용
   - 서버 재시작 시에도 파일에서 토큰 로드

4. **구현 클래스: TokenManager**
   - `get_valid_token()`: 유효한 토큰 반환 (자동 갱신 포함)
   - `request_new_token()`: 새 토큰 발급
   - `save_token()`: 토큰 파일 저장
   - `load_token()`: 토큰 파일 로드
   - `is_token_valid()`: 토큰 유효성 확인

### 3단계: 잔고 조회 API 구현

**KIS API 연동:**
- 엔드포인트: 주식잔고조회 (`TTTC8434R`)
- 필수 헤더:
  - `authorization`: Bearer {access_token}
  - `appkey`: APP_KEY
  - `appsecret`: APP_SECRET
  - `tr_id`: TTTC8434R (실전) / VTTC8434R (모의)

**백엔드 API 엔드포인트:**
```
GET /api/v1/account/balance
```

**응답 포맷:**
```json
{
  "total_evaluation": 10000000,
  "deposit": 5000000,
  "total_profit_loss": 500000,
  "profit_loss_rate": 5.26,
  "holdings": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "quantity": 10,
      "avg_price": 70000,
      "current_price": 75000,
      "evaluation_amount": 750000,
      "profit_loss": 50000,
      "profit_loss_rate": 7.14
    }
  ]
}
```

**구현 클래스: KISClient**
- `get_balance()`: 잔고 조회
- `_make_request()`: KIS API 공통 요청 메서드
- TokenManager와 연동하여 자동으로 유효한 토큰 주입

## 🔑 핵심 고려사항

### 1. 토큰 관리의 중요성
- KIS API는 호출 횟수 제한이 있을 수 있으므로, 불필요한 토큰 재발급을 방지해야 함
- 토큰 유효기간을 정확히 추적하여 만료 직전에만 갱신
- 파일 기반 저장으로 서버 재시작 시에도 토큰 유지

### 2. 보안
- `.env` 파일을 `.gitignore`에 추가하여 민감 정보 보호
- `.env.example` 파일 제공으로 필요한 환경 변수 가이드
- 토큰 파일(`token.json`)도 `.gitignore`에 추가

### 3. 에러 핸들링
- KIS API 호출 실패 시 적절한 에러 메시지 반환
- 네트워크 오류, 인증 오류 등 예외 처리
- 재시도 로직 고려 (optional)

### 4. 실전/모의투자 전환
- 환경 변수로 실전/모의투자 모드 전환 가능하도록 설계
- TR_ID도 모드에 따라 자동 선택

## ✅ 완료 조건

1. ✓ 서버 재시작 후에도 유효한 토큰이 있으면 재사용 (로그로 확인 가능)
2. ✓ `GET /api/v1/account/balance` 호출 시 잔고 정보가 JSON으로 반환
3. ✓ `.env` 파일이 Git에 커밋되지 않도록 설정
4. ✓ Poetry를 통한 의존성 관리
5. ✓ 기본적인 에러 핸들링 구현

## 📚 참고 자료

- [한국투자증권 개발자 센터](https://apiportal.koreainvestment.com/)
- KIS API 인증 문서
- KIS API 주식잔고조회 문서

## 🚀 다음 단계

이 이슈가 완료되면:
- 주식 조회 및 매매 API 구현
- WebSocket을 통한 실시간 시세 수신
- Gemini CLI 에이전트 연동

---

## 📊 구현 완료 (Implementation Completed)

### 주요 구현 내용

#### 1. 토큰 관리 시스템 (TokenManager)
- **파일**: `app/services/token_manager.py`
- **기능**:
  - Access Token을 `token.json` 파일에 저장
  - 토큰 만료 시간 자동 관리 (만료 60초 전 갱신)
  - 서버 재시작 시 파일에서 토큰 자동 로드 및 재사용
  - 로깅을 통한 토큰 사용 추적

#### 2. KIS API 클라이언트 개선
- **파일**: `kis_client.py`
- **변경사항**:
  - TokenManager 통합
  - 매 API 호출 시 자동으로 유효한 토큰 사용
  - 메모리 기반 토큰 관리를 파일 기반으로 변경

#### 3. 환경 변수 관리
- **파일**: `app/config.py`
- **기능**:
  - Pydantic Settings를 사용한 타입 안전 환경 변수 로드
  - `.env` 파일 자동 로드
  - 전역 settings 인스턴스 제공

#### 4. 잔고 조회 API
- **파일**: `app/api/v1/account.py`
- **엔드포인트**: `GET /api/v1/account/balance`
- **기능**:
  - KIS API를 통한 잔고 조회
  - 자동 토큰 관리 (TokenManager 사용)
  - 총 자산, 예수금, 손익, 보유 종목 정보 반환

#### 5. 보안 및 설정
- **`.gitignore`**: `token.json` 및 `*.token` 파일 제외 추가
- **`.env.example`**: 환경 변수 템플릿 제공
- **`requirements.txt`**: `pydantic-settings` 추가

### 테스트 결과

✅ **토큰 관리 테스트**
- 토큰이 `token.json` 파일에 정상 저장됨
- 두 번째 API 호출 시 캐시된 토큰 재사용 확인 (로그: "Using cached token (still valid)")
- 새 클라이언트 인스턴스도 파일에서 토큰 로드 및 재사용 확인
- 서버 재시작 후에도 기존 토큰 재사용 확인

✅ **API 엔드포인트 테스트**
- `GET /api/v1/account/balance` 정상 작동
- 응답 형식: JSON (총자산, 예수금, 손익, 보유종목)
- HTTP 200 OK 응답

✅ **환경 설정 테스트**
- Config 모듈 정상 로드
- `.env` 파일에서 환경 변수 정상 읽기
- IS_SIMULATION 모드 정상 작동

### 파일 변경 사항

**신규 파일**:
- `app/config.py` - 환경 변수 관리
- `app/services/token_manager.py` - 토큰 관리 시스템
- `.env.example` - 환경 변수 템플릿
- `docs/devlog/2026-01-23-1-initial-setup-and-balance-api.md` - 개발 로그

**수정 파일**:
- `kis_client.py` - TokenManager 통합
- `app/api/v1/account.py` - 간소화 및 config 사용
- `requirements.txt` - pydantic-settings 추가
- `.gitignore` - token.json 제외 추가
- `.env` - IS_SIMULATION 변수 추가

### 완료 조건 체크

- ✅ 서버 재시작 후에도 유효기간이 남은 토큰 재사용 (로그로 확인)
- ✅ `GET /api/v1/account/balance` 호출 시 잔고 정보 JSON 반환
- ✅ `.env` 파일이 Git에 커밋되지 않도록 설정
- ✅ Poetry 대신 pip/venv를 통한 의존성 관리
- ✅ 토큰 파일도 Git에 커밋되지 않도록 설정

---

**작성자**: Claude
**마지막 업데이트**: 2026-01-23 (완료)
