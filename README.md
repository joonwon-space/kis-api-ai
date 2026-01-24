# KIS API Backend

한국투자증권(Korea Investment & Securities) Open API를 활용한 FastAPI 백엔드 서비스

## 📋 소개

이 프로젝트는 한국투자증권 Open API를 래핑하여 다음 기능을 제공합니다:

- ✅ 토큰 자동 관리 및 캐싱
- ✅ 계좌 잔고 조회
- ✅ 국내/해외 주식 보유 내역 조회
- ✅ 주식 검색 및 실시간 시세 조회
- 🚧 주식 주문 (예정)
- 🚧 실시간 시세 WebSocket (예정)

## 🚀 빠른 시작

### 1. Docker Compose 사용 (권장)

가장 빠르고 간단한 방법입니다.

```bash
# 환경 변수 설정
cp kis_api_backend/.env.example kis_api_backend/.env
# .env 파일을 열어 KIS API 키 입력

# 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# API 접속
curl http://localhost:8000/health
```

### 2. Docker 직접 사용

```bash
# 이미지 빌드
docker build -t kis-api-backend ./kis_api_backend

# 컨테이너 실행
docker run -d \
  --name kis-api \
  --env-file ./kis_api_backend/.env \
  -p 8000:8000 \
  kis-api-backend

# 로그 확인
docker logs -f kis-api
```

### 3. 로컬 개발 환경

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
# .env 파일 편집하여 API 키 입력

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

## 🔑 환경 변수 설정

`.env` 파일에 다음 정보를 입력하세요:

```bash
# KIS API 인증 정보
APP_KEY=your_app_key_here
APP_SECRET=your_app_secret_here

# 계좌 정보
ACCOUNT_NO=12345678
ACNT_PRDT_CD=01

# 모드 설정 (true: 모의투자, false: 실전투자)
IS_SIMULATION=true
```

## 📚 API 문서

서버 실행 후 다음 주소에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 주요 엔드포인트

#### 계좌 관리
- `GET /api/v1/account/balance` - 계좌 잔고 조회
- `GET /api/v1/account/holdings/domestic` - 국내 주식 보유 내역
- `GET /api/v1/account/holdings/overseas` - 해외 주식 보유 내역

#### 주식 시세
- `GET /api/v1/stock/quote?keyword={종목명|코드}` - 주식 시세 조회
- `GET /api/v1/stock/debug/{종목코드}` - KIS API 원본 응답 (디버그용)

#### 헬스 체크
- `GET /health` - 서버 상태 확인
- `GET /` - API 정보

## 🐳 Docker 상세 사용법

### 이미지 빌드

```bash
# 프로덕션 이미지 빌드
docker build -t kis-api-backend:latest ./kis_api_backend

# 개발 이미지 빌드
docker build -f ./kis_api_backend/Dockerfile.dev -t kis-api-backend:dev ./kis_api_backend
```

### 컨테이너 관리

```bash
# 컨테이너 시작
docker-compose up -d

# 컨테이너 중지
docker-compose down

# 컨테이너 재시작
docker-compose restart

# 로그 실시간 확인
docker-compose logs -f api

# 컨테이너 상태 확인
docker-compose ps
```

### 헬스 체크

```bash
# 컨테이너 헬스 상태 확인
docker inspect --format='{{json .State.Health}}' kis-api-backend | jq

# 수동 헬스 체크
curl http://localhost:8000/health
```

### 이미지 분석

```bash
# 이미지 크기 확인
docker images kis-api-backend

# 레이어 확인
docker history kis-api-backend:latest
```

## 🛠️ 개발 가이드

### 개발 환경 설정

```bash
# 개발용 docker-compose 사용
docker-compose up -d

# 코드 변경 시 자동 재시작 (hot reload 활성화)
# docker-compose.yml에서 --reload 옵션 활성화됨
```

### 테스트 실행

```bash
# 로컬 환경
pytest

# Docker 환경
docker-compose exec api pytest
```

### 코드 스타일

프로젝트는 다음 컨벤션을 따릅니다:
- Black for code formatting
- isort for import sorting
- Conventional Commits for commit messages

## 📦 프로젝트 구조

```
kis-api-ai/
├── kis_api_backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── account.py      # 계좌 관련 엔드포인트
│   │   │       └── stock.py        # 주식 관련 엔드포인트
│   │   ├── schemas/
│   │   │   ├── account.py          # 계좌 스키마
│   │   │   ├── stock.py            # 주식 스키마
│   │   │   └── common.py           # 공통 스키마
│   │   ├── services/
│   │   │   ├── token_manager.py    # 토큰 관리
│   │   │   ├── stock_master_service.py  # 종목 마스터 데이터
│   │   │   └── stock_service.py    # 주식 시세 조회
│   │   ├── config.py               # 환경 변수 설정
│   │   └── main.py                 # FastAPI 앱
│   ├── kis_client.py               # KIS API 클라이언트
│   ├── Dockerfile                  # 프로덕션 Dockerfile
│   ├── Dockerfile.dev              # 개발용 Dockerfile
│   ├── requirements.txt            # 의존성 목록
│   └── .env.example                # 환경 변수 템플릿
├── docs/
│   └── devlog/                     # 개발 로그
├── docker-compose.yml              # Docker Compose 설정
└── README.md
```

## 🔐 보안

- `.env` 파일은 절대 커밋하지 마세요
- `token.json`은 자동으로 생성되며 `.gitignore`에 포함되어 있습니다
- Docker 컨테이너는 non-root 유저로 실행됩니다
- 민감한 정보는 환경 변수나 Kubernetes Secrets를 통해 주입하세요

## 📖 참고 자료

- [KIS Developers Portal](https://apiportal.koreainvestment.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)

## 📝 라이선스

This project is licensed under the MIT License.

## 👥 기여

이슈와 PR을 환영합니다!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 문의

이슈를 통해 문의해주세요.

---

**개발**: Claude Sonnet 4.5와 함께 AI 페어 프로그래밍으로 개발되었습니다.
