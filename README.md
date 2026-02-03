# KIS API Backend

[![Deploy to Cloud Run](https://github.com/joonwon-space/kis-api-ai/actions/workflows/deploy.yml/badge.svg)](https://github.com/joonwon-space/kis-api-ai/actions/workflows/deploy.yml)
[![Test](https://github.com/joonwon-space/kis-api-ai/actions/workflows/test.yml/badge.svg)](https://github.com/joonwon-space/kis-api-ai/actions/workflows/test.yml)

한국투자증권(Korea Investment & Securities) Open API를 활용한 FastAPI 백엔드 서비스

## 소개

이 프로젝트는 한국투자증권 Open API를 래핑하여 다음 기능을 제공합니다:

- 토큰 자동 관리 및 캐싱
- JWT 기반 사용자 인증
- 사용자별 KIS API 키 암호화 저장
- 계좌 잔고 조회
- 국내/해외 주식 보유 내역 조회
- 주식 검색 및 실시간 시세 조회
- 대시보드 (자산 요약, 보유 종목)

## 빠른 시작

### 1. Docker Compose 사용 (권장)

```bash
# 환경 변수 설정
cp kis_api_backend/.env.example kis_api_backend/.env
# .env 파일을 열어 필수 값 입력

# 컨테이너 시작
docker-compose up -d

# API 접속
curl http://localhost:8000/health
```

### 2. 로컬 개발 환경

```bash
# 프로젝트 클론
git clone https://github.com/joonwon-space/kis-api-ai.git
cd kis-api-ai/kis_api_backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 필수 값 입력

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

## 환경 변수 설정

`.env` 파일에 다음 정보를 입력하세요:

```bash
# KIS API 인증 정보 (선택 - 사용자별 키 사용 권장)
APP_KEY=your_app_key_here
APP_SECRET=your_app_secret_here
ACCOUNT_NO=12345678
ACNT_PRDT_CD=01

# 모드 설정 (true: 모의투자, false: 실전투자)
IS_SIMULATION=true

# JWT 인증 (필수)
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 암호화 키 (필수 - 사용자 API 키 암호화용)
# 생성: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your-fernet-encryption-key-here
```

## API 문서

서버 실행 후 다음 주소에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 주요 엔드포인트

#### 인증
- `POST /api/v1/auth/register` - 회원가입
- `POST /api/v1/auth/login` - 로그인 (JWT 토큰 발급)

#### 사용자 설정
- `POST /api/v1/settings/kis-credentials` - KIS API 키 등록
- `GET /api/v1/settings/kis-credentials` - KIS API 키 조회
- `DELETE /api/v1/settings/kis-credentials` - KIS API 키 삭제

#### 대시보드
- `GET /api/v1/dashboard/summary` - 자산 요약 (총 자산, 수익률)
- `GET /api/v1/dashboard/holdings` - 보유 종목 목록

#### 계좌 관리
- `GET /api/v1/account/balance` - 계좌 잔고 조회
- `GET /api/v1/account/holdings/domestic` - 국내 주식 보유 내역
- `GET /api/v1/account/holdings/overseas` - 해외 주식 보유 내역

#### 주식 시세
- `GET /api/v1/stock/quote?keyword={종목명|코드}` - 주식 시세 조회

#### 헬스 체크
- `GET /health` - 서버 상태 확인

## 프로젝트 구조

```
kis-api-ai/
├── kis_api_backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py           # 인증 (회원가입/로그인)
│   │   │   │   ├── dashboard.py      # 대시보드
│   │   │   │   └── user_settings.py  # 사용자 설정
│   │   │   ├── account.py            # 계좌 관련
│   │   │   └── stock.py              # 주식 시세
│   │   ├── core/
│   │   │   ├── security.py           # JWT, 암호화
│   │   │   └── exceptions.py         # 예외 정의
│   │   ├── db/                       # 데이터베이스 설정
│   │   ├── models/                   # SQLModel 모델
│   │   ├── schemas/                  # Pydantic 스키마
│   │   ├── services/                 # 비즈니스 로직
│   │   ├── config.py                 # 환경 변수 설정
│   │   └── main.py                   # FastAPI 앱
│   ├── tests/                        # 테스트
│   ├── Dockerfile
│   └── requirements.txt
├── docs/devlog/                      # 개발 로그
├── docker-compose.yml
├── CLAUDE.md                         # Claude Code 가이드
└── README.md
```

## 개발 가이드

### 테스트 실행

```bash
# 로컬 환경
pytest

# 커버리지 확인
pytest --cov=app --cov-report=html

# Docker 환경
docker-compose exec api pytest
```

### 코드 스타일

- PEP 8 준수
- Type hints 필수
- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)

## CI/CD 자동 배포

GitHub Actions를 통해 Google Cloud Run으로 자동 배포됩니다.

```
main 브랜치 push → GitHub Actions → Docker 빌드 → Artifact Registry → Cloud Run
```

### GitHub Secrets 설정

| Secret 이름 | 설명 |
|------------|------|
| `GCP_PROJECT_ID` | GCP 프로젝트 ID |
| `GCP_SA_KEY` | Service Account JSON 키 |
| `APP_KEY` | KIS API 키 |
| `APP_SECRET` | KIS API 시크릿 |
| `ACCOUNT_NO` | 계좌번호 |
| `ACNT_PRDT_CD` | 계좌 상품 코드 |
| `SECRET_KEY` | JWT 비밀키 |
| `ENCRYPTION_KEY` | Fernet 암호화 키 |

## 보안

- `.env` 파일은 절대 커밋하지 마세요
- `token.json`은 `.gitignore`에 포함되어 있습니다
- Docker 컨테이너는 non-root 유저로 실행됩니다
- 사용자 API 키는 Fernet으로 암호화되어 저장됩니다

## 참고 자료

- [KIS Developers Portal](https://apiportal.koreainvestment.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 라이선스

This project is licensed under the MIT License.

## 기여

이슈와 PR을 환영합니다!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**개발**: Claude와 함께 AI 페어 프로그래밍으로 개발되었습니다.
