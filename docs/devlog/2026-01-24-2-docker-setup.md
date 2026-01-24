# Issue #5: Docker 컨테이너화 설정

**날짜**: 2026-01-24
**이슈 번호**: #5
**상태**: ✅ Completed

## 📋 요약

KIS API Backend를 Docker 컨테이너로 실행 가능하도록 설정합니다. 프로덕션 환경 배포를 위한 Dockerfile과 개발 환경을 위한 docker-compose.yml을 작성합니다.

## 🎯 목표

1. 프로덕션용 Dockerfile 작성
2. 개발 환경용 docker-compose.yml 작성
3. .dockerignore 설정
4. 환경 변수 주입 방식 설계
5. 컨테이너 헬스 체크 구현

## 📐 구현 계획

### 패키지 관리 방식 현황 확인

**현재 사용 중**: `requirements.txt` ✅
- 파일: `/kis_api_backend/requirements.txt`
- 의존성: fastapi, uvicorn, httpx, pydantic-settings 등

**Poetry는 사용하지 않음** (향후 전환 고려 가능)

### 1단계: Dockerfile 작성 전략

#### 선택지 비교: Multi-stage Build vs Single-stage Build

**1. Multi-stage Build** ✅ (추천)

```dockerfile
# Stage 1: Builder (의존성 설치)
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime (최종 이미지)
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**장점:**
- 최종 이미지 크기 감소 (build 도구 제외)
- 레이어 캐싱으로 재빌드 속도 향상
- 보안 향상 (빌드 도구 미포함)

**단점:**
- Dockerfile 복잡도 증가
- 단순한 앱에는 오버엔지니어링

**2. Single-stage Build**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**장점:**
- 간단하고 이해하기 쉬움
- 디버깅 용이

**단점:**
- 이미지 크기가 큼
- 불필요한 빌드 도구 포함

**결정**: **Multi-stage Build** 사용 ✅
- 프로덕션 환경에서 이미지 크기와 보안이 중요
- FastAPI 앱은 런타임에 pip, gcc 등 불필요

#### Python 베이스 이미지 선택

**선택지:**
1. `python:3.11` - Full 이미지 (~900MB)
2. `python:3.11-slim` - 최소 이미지 (~120MB) ✅
3. `python:3.11-alpine` - 초경량 (~50MB)

**결정**: **python:3.11-slim** ✅

**이유:**
- Alpine은 musl libc로 인한 호환성 문제 (일부 C 확장 패키지)
- slim은 충분히 작으면서도 호환성 보장
- httpx, uvicorn 등이 문제없이 작동

#### 의존성 설치 최적화

**레이어 캐싱 활용:**
```dockerfile
# 의존성 파일만 먼저 복사 (자주 변경되지 않음)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사 (자주 변경됨)
COPY . .
```

**설명:**
- requirements.txt가 변경되지 않으면 의존성 설치 레이어 재사용
- 소스 코드만 변경 시 빠른 재빌드 가능

#### 보안 고려사항

1. **Non-root 유저 사용**
```dockerfile
RUN adduser --disabled-password --gecos "" appuser
USER appuser
```

2. **민감 정보 제외**
- `.env`, `token.json`은 빌드 시 포함하지 않음
- 런타임에 환경 변수 또는 볼륨 마운트로 주입

3. **최소 권한 원칙**
- 필요한 파일만 COPY
- .dockerignore로 불필요한 파일 제외

### 2단계: .dockerignore 작성

**목적:**
- Docker 빌드 컨텍스트 크기 최소화
- 민감 정보 보호
- 빌드 속도 향상

**포함 내용:**

```dockerignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
*.egg-info/

# 환경 설정 (민감 정보)
.env
.env.*
!.env.example
token.json
*.token

# 개발 도구
.git/
.github/
.vscode/
.idea/
*.md
docs/

# 테스트
.pytest_cache/
.coverage
htmlcov/
tests/

# OS
.DS_Store
Thumbs.db

# Docker
Dockerfile
docker-compose.yml
.dockerignore
```

**설명:**
- `.env` 제외: 런타임에 환경 변수로 주입
- `venv/` 제외: 컨테이너 내부에서 새로 설치
- `tests/` 제외: 프로덕션 이미지에 불필요
- `.env.example`은 포함 (문서용)

### 3단계: 환경 변수 주입 방식

**선택지 비교:**

| 방식 | 장점 | 단점 | 추천 |
|------|------|------|------|
| **1. docker run -e** | 간단함 | 매번 입력 필요 | 개발 |
| **2. --env-file** | .env 재사용 가능 | 파일 관리 필요 | 개발 ✅ |
| **3. Docker Secrets** | 보안 강화 | Swarm 필요 | 프로덕션 |
| **4. K8s Secrets** | 자동화 가능 | K8s 환경 필요 | 프로덕션 ✅ |

**개발 환경: --env-file** ✅
```bash
docker run --env-file .env -p 8000:8000 kis-api-backend
```

**프로덕션 환경: Kubernetes Secrets** ✅
```yaml
env:
  - name: APP_KEY
    valueFrom:
      secretKeyRef:
        name: kis-api-secrets
        key: app_key
```

### 4단계: docker-compose.yml 작성 (개발용)

**목적:**
- 로컬 개발 환경 간소화
- 볼륨 마운트로 코드 변경 즉시 반영
- 환경 변수 자동 로드

**구성:**

```yaml
version: '3.8'

services:
  api:
    build:
      context: ./kis_api_backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - ./kis_api_backend/.env
    volumes:
      # 소스 코드 마운트 (개발 시 hot reload)
      - ./kis_api_backend/app:/app/app
      # 토큰 파일 영속화
      - ./kis_api_backend/token.json:/app/token.json
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**특징:**
- `--reload`: 코드 변경 시 자동 재시작
- `volumes`: 로컬 파일 변경 즉시 반영
- `healthcheck`: 컨테이너 상태 모니터링
- `token.json` 마운트: 토큰 캐시 영속화

### 5단계: 헬스 체크 구현

**FastAPI에 헬스 체크 엔드포인트 이미 있음:**
```python
@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Docker 헬스 체크:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

**또는 Python으로:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"
```

## 🔑 핵심 설계 결정

### 1. Poetry vs requirements.txt for Docker

**현재 상태**: requirements.txt 사용 중

**Docker 관점에서 비교:**

#### Poetry 방식

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Poetry 설치
RUN pip install poetry

# 의존성 파일 복사
COPY pyproject.toml poetry.lock ./

# 의존성 설치 (가상환경 생성 안함)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**장점:**
- 의존성 잠금 파일(poetry.lock)로 재현 가능한 빌드
- 개발/프로덕션 의존성 분리 (`--no-dev`)
- 의존성 해결 자동화

**단점:**
- 이미지 크기 증가 (Poetry 도구 포함)
- 빌드 시간 증가 (Poetry 설치 + 의존성 해결)
- 복잡도 증가

#### requirements.txt 방식 (현재 사용) ✅

```dockerfile
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**장점:**
- 간단하고 빠른 빌드
- 이미지 크기 최소화
- 표준 Python 도구만 사용

**단점:**
- 의존성 잠금 없음 (버전 고정 필요)
- 개발/프로덕션 의존성 분리 어려움

#### Poetry + requirements.txt 하이브리드 (추천) ✅

**로컬 개발**: Poetry 사용
```bash
poetry add fastapi
poetry install
```

**Docker 빌드**: requirements.txt 변환
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

**Dockerfile**:
```dockerfile
# requirements.txt 사용 (Poetry 설치 불필요)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**장점:**
- 로컬에서는 Poetry의 편리함 활용
- Docker 빌드는 빠르고 가벼움
- 최선의 양립

**단점:**
- requirements.txt 동기화 필요
- CI/CD에 export 단계 추가

### 결론: 현재 프로젝트 권장 사항

**단기 (현재)**: **requirements.txt 유지** ✅
- 이미 requirements.txt 사용 중
- 프로젝트 규모가 작아 Poetry 불필요
- Docker 빌드 단순성 우선

**중기 (확장 시)**: **Poetry + Docker 하이브리드**
- 로컬: Poetry로 의존성 관리
- Docker: `poetry export`로 requirements.txt 생성
- CI/CD에서 자동 export

**장기 (대규모)**: **Poetry 완전 도입 + Multi-stage**
- 의존성 복잡도 증가 시
- Monorepo 또는 마이크로서비스 전환 시

## 📋 Dockerfile 최종 설계

### 프로덕션 Dockerfile

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Non-root 유저 생성
RUN adduser --disabled-password --gecos "" appuser

# 빌더에서 설치된 패키지 복사
COPY --from=builder /root/.local /home/appuser/.local

# 소스 코드 복사
COPY --chown=appuser:appuser . .

# PATH 설정
ENV PATH=/home/appuser/.local/bin:$PATH

# 유저 전환
USER appuser

# 포트 노출
EXPOSE 8000

# 헬스 체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

# 앱 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**특징:**
- Multi-stage build로 이미지 크기 최소화
- Non-root 유저로 보안 강화
- 헬스 체크 포함
- 레이어 캐싱 최적화

### 개발 Dockerfile.dev (선택적)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 개발 도구 설치
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스는 볼륨 마운트로 제공

# 개발 서버 실행 (hot reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## 📦 .dockerignore 최종 내용

```dockerignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 가상 환경
venv/
env/
ENV/
env.bak/
venv.bak/

# 환경 설정 및 민감 정보
.env
.env.*
!.env.example
token.json
*.token

# 테스트
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.tox/
.hypothesis/
tests/

# 개발 도구
.git/
.github/
.gitignore
.vscode/
.idea/
*.swp
*.swo
*~

# 문서
*.md
docs/
*.rst

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Docker 관련
Dockerfile*
docker-compose*.yml
.dockerignore

# 로그
*.log
logs/

# CI/CD
.gitlab-ci.yml
.travis.yml
Jenkinsfile
```

## 🚀 사용 방법 (구현 후)

### 이미지 빌드

```bash
# 프로덕션 이미지
docker build -t kis-api-backend:latest ./kis_api_backend

# 개발 이미지
docker build -f Dockerfile.dev -t kis-api-backend:dev ./kis_api_backend
```

### 컨테이너 실행

```bash
# 프로덕션 (환경 변수 파일 사용)
docker run -d \
  --name kis-api \
  --env-file ./kis_api_backend/.env \
  -p 8000:8000 \
  kis-api-backend:latest

# 개발 (볼륨 마운트)
docker run -d \
  --name kis-api-dev \
  --env-file ./kis_api_backend/.env \
  -p 8000:8000 \
  -v $(pwd)/kis_api_backend:/app \
  kis-api-backend:dev
```

### docker-compose 사용

```bash
# 개발 환경 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

## ✅ 완료 조건

- ✅ Dockerfile 작성 (Multi-stage build)
- ✅ Dockerfile.dev 작성 (개발용)
- ✅ .dockerignore 작성
- ✅ docker-compose.yml 작성 (개발용)
- ✅ README에 Docker 사용법 추가
- ⏳ 이미지 빌드 및 실행 테스트 (사용자 환경에서 테스트 필요)
- ⏳ 헬스 체크 동작 확인 (사용자 환경에서 테스트 필요)
- ⏳ 환경 변수 주입 테스트 (사용자 환경에서 테스트 필요)
- ⏳ 토큰 파일 영속화 테스트 (사용자 환경에서 테스트 필요)

## 🔍 테스트 계획

### 1. 빌드 테스트
```bash
docker build -t kis-api-backend:test ./kis_api_backend
docker images kis-api-backend:test  # 이미지 크기 확인
```

### 2. 실행 테스트
```bash
docker run -d --name test-api --env-file .env -p 8000:8000 kis-api-backend:test
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/account/balance
```

### 3. 헬스 체크 테스트
```bash
docker inspect --format='{{json .State.Health}}' test-api | jq
```

### 4. 레이어 분석
```bash
docker history kis-api-backend:test
```

## 📚 참고 자료

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Python Docker Image Official Guide](https://hub.docker.com/_/python)
- [FastAPI in Containers - Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)

## 🚀 다음 단계

이 이슈가 완료되면:
- Kubernetes 배포 설정 (Deployment, Service, Ingress)
- CI/CD 파이프라인 구성 (GitHub Actions)
- 컨테이너 로깅 및 모니터링 설정
- Docker Hub / ECR에 이미지 푸시

---

## 📊 구현 완료 (Implementation Completed)

### 주요 구현 내용

#### 1. 프로덕션 Dockerfile
- **파일**: `kis_api_backend/Dockerfile`
- **특징**:
  - Multi-stage build (builder + runtime)
  - python:3.11-slim 베이스 이미지
  - Non-root 유저 (appuser)
  - 레이어 캐싱 최적화
  - 헬스 체크 내장
  - 예상 이미지 크기: ~150MB

#### 2. 개발용 Dockerfile
- **파일**: `kis_api_backend/Dockerfile.dev`
- **특징**:
  - Single-stage build (간소화)
  - curl 포함 (헬스 체크용)
  - 소스는 볼륨 마운트로 제공
  - Hot reload 활성화

#### 3. .dockerignore
- **파일**: `kis_api_backend/.dockerignore`
- **제외 항목**:
  - 가상환경 (venv/)
  - 캐시 파일 (__pycache__/)
  - 민감 정보 (.env, token.json)
  - 테스트 파일 (tests/)
  - 개발 도구 (.git/, .vscode/)
  - 문서 (*.md, docs/)

#### 4. docker-compose.yml
- **파일**: `docker-compose.yml` (프로젝트 루트)
- **특징**:
  - 환경 변수 자동 로드 (.env)
  - 소스 코드 볼륨 마운트 (hot reload)
  - 토큰 파일 영속화
  - 헬스 체크 설정
  - 네트워크 격리 (kis-network)
  - 자동 재시작 (unless-stopped)

#### 5. README 업데이트
- **파일**: `README.md`
- **추가 내용**:
  - 프로젝트 소개 및 기능 목록
  - Docker Compose 사용법
  - Docker 직접 사용법
  - 로컬 개발 환경 설정
  - API 문서 접근 방법
  - 주요 엔드포인트 목록
  - 프로젝트 구조 다이어그램
  - 보안 가이드

### 파일 변경 사항

**신규 파일**:
- `kis_api_backend/Dockerfile` - 프로덕션 이미지
- `kis_api_backend/Dockerfile.dev` - 개발 이미지
- `kis_api_backend/.dockerignore` - 빌드 최적화
- `docker-compose.yml` - 개발 환경 오케스트레이션

**수정 파일**:
- `README.md` - 프로젝트 문서 전면 개편

### 기술 스택 결정

| 항목 | 선택 | 이유 |
|------|------|------|
| 베이스 이미지 | python:3.11-slim | 크기와 호환성 균형 |
| 빌드 방식 | Multi-stage | 이미지 크기 최소화 |
| 패키지 관리 | requirements.txt | 현재 사용 중, 단순함 |
| 유저 | Non-root (appuser) | 보안 강화 |
| 헬스 체크 | httpx + /health | 기존 엔드포인트 활용 |

### 사용 방법

#### 빠른 시작 (Docker Compose)
```bash
# 환경 변수 설정
cp kis_api_backend/.env.example kis_api_backend/.env
# .env 편집하여 API 키 입력

# 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 헬스 체크
curl http://localhost:8000/health
```

#### 프로덕션 이미지 빌드
```bash
docker build -t kis-api-backend:latest ./kis_api_backend
docker run -d --name kis-api --env-file .env -p 8000:8000 kis-api-backend:latest
```

### 예상 성능

- **이미지 크기**: ~150MB (Multi-stage build)
- **빌드 시간**: ~30-60초 (캐시 미사용 시)
- **재빌드 시간**: ~5-10초 (소스만 변경 시)
- **컨테이너 시작**: ~5초
- **메모리 사용량**: ~100-150MB (idle)

### 보안 강화

1. **Non-root 유저**: appuser로 실행
2. **민감 정보 제외**: .env, token.json은 런타임 주입
3. **최소 권한**: 필요한 파일만 COPY
4. **레이어 최소화**: Multi-stage build
5. **취약점 감소**: slim 이미지 사용

---

**브랜치**: `feature/issue-5-docker-setup`
**PR**: (예정)
**작성자**: Claude
**마지막 업데이트**: 2026-01-24 (완료)
