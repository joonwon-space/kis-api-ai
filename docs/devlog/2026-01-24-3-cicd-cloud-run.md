# Issue #8: GitHub Actions를 이용한 Cloud Run 자동 배포 CI/CD 파이프라인 구축

**날짜**: 2026-01-24
**이슈 번호**: #8
**상태**: 📝 Planning

## 📋 요약

GitHub에 코드를 푸시하면 자동으로 Docker 이미지를 빌드하여 Google Cloud Run에 배포되는 CI/CD 파이프라인을 구축합니다. 수동 배포 과정을 제거하여 개발 생산성을 높이고 배포 프로세스를 안정화합니다.

## 🎯 목표

1. GitHub Actions 워크플로우 작성
2. GCP 서비스 계정 설정 및 권한 부여
3. Artifact Registry에 이미지 자동 푸시
4. Cloud Run 자동 배포
5. 환경 변수 및 시크릿 관리

## 📐 현재 상태 확인

### GCP 연결 상태
- ✅ gcloud CLI 설치 완료
- ✅ 계정 인증 완료 (`jwon3711@gmail.com`)
- ✅ 프로젝트 설정 완료 (`kis-ai-485303`)
- ✅ Docker 인증 설정 완료 (GCR)

### 필요한 GCP 리소스
1. **Artifact Registry**: Docker 이미지 저장소
2. **Cloud Run**: 컨테이너 실행 환경
3. **Service Account**: GitHub Actions용 인증

## 📐 구현 계획

### 1단계: GCP 리소스 준비

#### 1-1. Artifact Registry 저장소 생성

**선택지:**
- **GCR (Container Registry)**: 기존 방식, 곧 deprecated
- **Artifact Registry**: 새로운 표준 ✅

**결정**: Artifact Registry 사용

```bash
# Artifact Registry API 활성화
gcloud services enable artifactregistry.googleapis.com

# 저장소 생성
gcloud artifacts repositories create kis-api-repo \
  --repository-format=docker \
  --location=asia-northeast3 \
  --description="KIS API Backend Docker images"

# 저장소 확인
gcloud artifacts repositories list
```

**레지스트리 주소**:
```
asia-northeast3-docker.pkg.dev/kis-ai-485303/kis-api-repo
```

#### 1-2. Cloud Run 서비스 생성 (초기 배포)

```bash
# Cloud Run API 활성화
gcloud services enable run.googleapis.com

# 초기 서비스 생성 (이미지 없이도 가능)
gcloud run deploy kis-api-backend \
  --image gcr.io/cloudrun/hello \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --port 8000 \
  --set-env-vars="IS_SIMULATION=true"
```

**또는 첫 배포는 로컬에서:**
```bash
# 1. 이미지 빌드
docker build -t asia-northeast3-docker.pkg.dev/kis-ai-485303/kis-api-repo/kis-api-backend:latest \
  ./kis_api_backend

# 2. Docker 인증
gcloud auth configure-docker asia-northeast3-docker.pkg.dev

# 3. 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/kis-ai-485303/kis-api-repo/kis-api-backend:latest

# 4. Cloud Run 배포
gcloud run deploy kis-api-backend \
  --image asia-northeast3-docker.pkg.dev/kis-ai-485303/kis-api-repo/kis-api-backend:latest \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --port 8000
```

#### 1-3. Service Account 생성 및 권한 부여

**목적**: GitHub Actions가 GCP에 접근할 수 있는 전용 계정

```bash
# 서비스 계정 생성
gcloud iam service-accounts create github-actions-deployer \
  --display-name="GitHub Actions Deployer" \
  --description="Service account for GitHub Actions CI/CD"

# 권한 부여
# 1. Artifact Registry Writer (이미지 푸시)
gcloud projects add-iam-policy-binding kis-ai-485303 \
  --member="serviceAccount:github-actions-deployer@kis-ai-485303.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# 2. Cloud Run Developer (배포)
gcloud projects add-iam-policy-binding kis-ai-485303 \
  --member="serviceAccount:github-actions-deployer@kis-ai-485303.iam.gserviceaccount.com" \
  --role="roles/run.developer"

# 3. Service Account User (SA 사용 권한)
gcloud projects add-iam-policy-binding kis-ai-485303 \
  --member="serviceAccount:github-actions-deployer@kis-ai-485303.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# 4. Storage Admin (Cloud Build 사용 시 필요)
gcloud projects add-iam-policy-binding kis-ai-485303 \
  --member="serviceAccount:github-actions-deployer@kis-ai-485303.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# JSON 키 생성
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-deployer@kis-ai-485303.iam.gserviceaccount.com
```

**보안 주의사항:**
- JSON 키 파일은 절대 Git에 커밋하지 않음
- GitHub Secrets에만 저장
- 로컬에서는 즉시 삭제

### 2단계: GitHub Secrets 설정

**GitHub Repository → Settings → Secrets and variables → Actions**

| Secret 이름 | 값 | 설명 |
|------------|-----|------|
| `GCP_PROJECT_ID` | `kis-ai-485303` | GCP 프로젝트 ID |
| `GCP_SA_KEY` | `{JSON 키 내용}` | 서비스 계정 JSON 키 전체 |
| `GCP_REGION` | `asia-northeast3` | Cloud Run 배포 리전 |
| `GCP_REGISTRY` | `asia-northeast3-docker.pkg.dev` | Artifact Registry 주소 |
| `APP_KEY` | `{KIS API Key}` | 한국투자증권 API 키 |
| `APP_SECRET` | `{KIS API Secret}` | 한국투자증권 API 시크릿 |
| `ACCOUNT_NO` | `{계좌번호}` | 계좌번호 |
| `ACNT_PRDT_CD` | `01` | 계좌 상품 코드 |

### 3단계: GitHub Actions Workflow 작성

#### 워크플로우 파일 구조

```
.github/
└── workflows/
    ├── deploy.yml        # 프로덕션 배포 (main 브랜치)
    └── test.yml          # 테스트 (PR)
```

#### deploy.yml 설계

**트리거**:
- `main` 브랜치에 push
- `kis_api_backend/` 경로 변경 시에만 (선택적)

**Jobs**:
1. **test**: 테스트 실행 (선택적)
2. **build-and-deploy**: 빌드 및 배포

**주요 액션**:
- `actions/checkout@v4`: 코드 체크아웃
- `google-github-actions/auth@v2`: GCP 인증
- `google-github-actions/setup-gcloud@v2`: gcloud CLI 설정
- `docker/setup-buildx-action@v3`: Docker Buildx 설정
- `google-github-actions/deploy-cloudrun@v2`: Cloud Run 배포

### 4단계: Workflow 파일 작성

**`.github/workflows/deploy.yml`**:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main
    paths:
      - 'kis_api_backend/**'
      - '.github/workflows/deploy.yml'

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: ${{ secrets.GCP_REGION }}
  SERVICE_NAME: kis-api-backend
  REGISTRY: ${{ secrets.GCP_REGISTRY }}

jobs:
  deploy:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      id-token: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker for Artifact Registry
        run: |
          gcloud auth configure-docker ${{ env.REGISTRY }}

      - name: Build Docker image
        run: |
          docker build \
            -t ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/kis-api-repo/${{ env.SERVICE_NAME }}:${{ github.sha }} \
            -t ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/kis-api-repo/${{ env.SERVICE_NAME }}:latest \
            ./kis_api_backend

      - name: Push Docker image
        run: |
          docker push ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/kis-api-repo/${{ env.SERVICE_NAME }}:${{ github.sha }}
          docker push ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/kis-api-repo/${{ env.SERVICE_NAME }}:latest

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: ${{ env.SERVICE_NAME }}
          image: ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/kis-api-repo/${{ env.SERVICE_NAME }}:${{ github.sha }}
          region: ${{ env.REGION }}
          flags: |
            --port=8000
            --allow-unauthenticated
            --min-instances=0
            --max-instances=10
            --memory=512Mi
            --cpu=1
          secrets: |
            APP_KEY=${{ secrets.APP_KEY }}:latest
            APP_SECRET=${{ secrets.APP_SECRET }}:latest
            ACCOUNT_NO=${{ secrets.ACCOUNT_NO }}:latest
            ACNT_PRDT_CD=${{ secrets.ACNT_PRDT_CD }}:latest
          env_vars: |
            IS_SIMULATION=true

      - name: Show deployment URL
        run: |
          echo "Deployment successful!"
          gcloud run services describe ${{ env.SERVICE_NAME }} \
            --region=${{ env.REGION }} \
            --format='value(status.url)'
```

### 5단계: 환경 변수 관리 전략

#### 방법 비교

| 방법 | 장점 | 단점 | 추천 |
|------|------|------|------|
| **1. Cloud Run 환경 변수** | 간단함 | 보안 취약 | 비밀 아닌 값만 |
| **2. GitHub Secrets** | GitHub 통합 | Cloud Run에서 직접 접근 불가 | 배포 시에만 |
| **3. Secret Manager** | 가장 안전 | 설정 복잡 | 프로덕션 ✅ |

#### Secret Manager 사용 (권장)

```bash
# Secret Manager API 활성화
gcloud services enable secretmanager.googleapis.com

# 시크릿 생성
echo -n "your-app-key" | gcloud secrets create app-key --data-file=-
echo -n "your-app-secret" | gcloud secrets create app-secret --data-file=-
echo -n "12345678" | gcloud secrets create account-no --data-file=-
echo -n "01" | gcloud secrets create acnt-prdt-cd --data-file=-

# Cloud Run에 시크릿 접근 권한 부여
gcloud secrets add-iam-policy-binding app-key \
  --member="serviceAccount:github-actions-deployer@kis-ai-485303.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Cloud Run 배포 시 시크릿 마운트
gcloud run deploy kis-api-backend \
  --update-secrets=APP_KEY=app-key:latest \
  --update-secrets=APP_SECRET=app-secret:latest \
  --update-secrets=ACCOUNT_NO=account-no:latest \
  --update-secrets=ACNT_PRDT_CD=acnt-prdt-cd:latest
```

**Workflow에서 Secret Manager 사용**:

```yaml
secrets: |
  APP_KEY=app-key:latest
  APP_SECRET=app-secret:latest
  ACCOUNT_NO=account-no:latest
  ACNT_PRDT_CD=acnt-prdt-cd:latest
```

### 6단계: 테스트 워크플로우 (선택적)

**`.github/workflows/test.yml`**:

```yaml
name: Test

on:
  pull_request:
    paths:
      - 'kis_api_backend/**'

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd kis_api_backend
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd kis_api_backend
          pytest tests/ -v --cov=app

      - name: Build Docker image (test)
        run: |
          docker build -t kis-api-backend:test ./kis_api_backend
```

## 🔑 핵심 설계 결정

### 1. Artifact Registry vs GCR

| 항목 | GCR | Artifact Registry |
|------|-----|-------------------|
| 상태 | Deprecated | 현재 표준 ✅ |
| 기능 | Docker만 | Docker + Maven + npm 등 |
| 가격 | 저렴 | 조금 비쌈 |
| 권장 | 기존 프로젝트 | 신규 프로젝트 ✅ |

**결정**: Artifact Registry 사용

### 2. Workload Identity vs JSON Key

| 방법 | 보안 | 설정 복잡도 | 추천 |
|------|------|------------|------|
| **JSON Key** | 중간 | 쉬움 | 시작 단계 ✅ |
| **Workload Identity** | 높음 | 복잡 | 프로덕션 |

**결정**: JSON Key로 시작 (향후 Workload Identity 전환 고려)

### 3. 배포 전략

**Blue-Green vs Rolling Update vs Canary**

**Cloud Run 기본 동작**: **Traffic Split (Canary 가능)**

```yaml
# 기본: 모든 트래픽을 새 리비전으로
--no-traffic  # 트래픽 보내지 않음 (수동 전환)

# Canary: 트래픽 분산
gcloud run services update-traffic kis-api-backend \
  --to-revisions=REVISION-001=90,REVISION-002=10
```

**결정**: 기본 배포 (자동 100% 전환) → 안정화 후 Canary 도입

### 4. 비용 최적화

**Cloud Run 설정**:
- `--min-instances=0`: 사용하지 않을 때 0으로 스케일 (비용 절감)
- `--max-instances=10`: 최대 인스턴스 제한
- `--memory=512Mi`: 메모리 제한 (필요에 따라 조정)
- `--cpu=1`: CPU 제한

**예상 비용** (asia-northeast3):
- 요청 없을 때: $0/월
- 요청 있을 때: 약 $5-20/월 (트래픽에 따라)

## 📋 구현 체크리스트

### GCP 설정
- [ ] Artifact Registry API 활성화
- [ ] Artifact Registry 저장소 생성
- [ ] Cloud Run API 활성화
- [ ] Secret Manager API 활성화 (선택적)
- [ ] Service Account 생성
- [ ] Service Account 권한 부여
- [ ] JSON 키 생성 및 다운로드

### GitHub 설정
- [ ] Repository Secrets 등록
  - [ ] GCP_PROJECT_ID
  - [ ] GCP_SA_KEY
  - [ ] GCP_REGION
  - [ ] GCP_REGISTRY
  - [ ] APP_KEY, APP_SECRET, ACCOUNT_NO, ACNT_PRDT_CD
- [ ] `.github/workflows/deploy.yml` 작성
- [ ] `.github/workflows/test.yml` 작성 (선택적)

### 초기 배포
- [ ] 로컬에서 첫 이미지 빌드 및 푸시
- [ ] Cloud Run 서비스 초기 생성
- [ ] 배포 URL 확인
- [ ] Health check 확인

### 자동화 테스트
- [ ] main 브랜치에 푸시하여 워크플로우 트리거
- [ ] GitHub Actions 로그 확인
- [ ] 이미지가 Artifact Registry에 푸시되었는지 확인
- [ ] Cloud Run에 새 리비전 배포 확인
- [ ] 배포된 서비스 접속 테스트

## ✅ 완료 조건

1. ✅ `git push origin main` 시 GitHub Actions 워크플로우 자동 실행
2. ✅ 워크플로우가 성공적으로 완료 (초록색 체크)
3. ✅ Artifact Registry에 새 이미지 업로드 확인
4. ✅ Cloud Run에 새 리비전 배포 확인
5. ✅ 배포된 URL에서 API 정상 작동 확인
   - `GET https://{service-url}/health` → 200 OK
   - `GET https://{service-url}/docs` → Swagger UI 표시

## 🧪 테스트 계획

### 1. 로컬 테스트
```bash
# Docker 이미지 빌드
docker build -t test-image ./kis_api_backend

# 로컬 실행
docker run -p 8000:8000 --env-file kis_api_backend/.env test-image

# Health check
curl http://localhost:8000/health
```

### 2. GCP 테스트
```bash
# 이미지 푸시
docker tag test-image asia-northeast3-docker.pkg.dev/kis-ai-485303/kis-api-repo/kis-api-backend:test
docker push asia-northeast3-docker.pkg.dev/kis-ai-485303/kis-api-repo/kis-api-backend:test

# Cloud Run 배포
gcloud run deploy kis-api-backend-test \
  --image asia-northeast3-docker.pkg.dev/kis-ai-485303/kis-api-repo/kis-api-backend:test \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated
```

### 3. CI/CD 테스트
```bash
# 1. 테스트 브랜치 생성
git checkout -b test/cicd

# 2. 워크플로우 파일 작성
# .github/workflows/deploy.yml

# 3. 커밋 및 푸시
git add .github/workflows/
git commit -m "ci: Add Cloud Run deployment workflow"
git push origin test/cicd

# 4. PR 생성 및 머지
gh pr create --title "ci: Cloud Run CI/CD" --body "Testing"
gh pr merge --squash
```

## 🔍 트러블슈팅

### 문제 1: 권한 오류
```
ERROR: (gcloud.run.deploy) PERMISSION_DENIED
```

**해결**:
```bash
# 서비스 계정 권한 재확인
gcloud projects get-iam-policy kis-ai-485303 \
  --flatten="bindings[].members" \
  --filter="bindings.members:github-actions-deployer@"

# 누락된 권한 추가
gcloud projects add-iam-policy-binding kis-ai-485303 \
  --member="serviceAccount:github-actions-deployer@kis-ai-485303.iam.gserviceaccount.com" \
  --role="roles/run.developer"
```

### 문제 2: Docker 푸시 실패
```
ERROR: denied: Permission "artifactregistry.repositories.uploadArtifacts" denied
```

**해결**:
```bash
# Artifact Registry 권한 추가
gcloud projects add-iam-policy-binding kis-ai-485303 \
  --member="serviceAccount:github-actions-deployer@kis-ai-485303.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

### 문제 3: 환경 변수 누락
```
ERROR: Missing required environment variable: APP_KEY
```

**해결**:
- GitHub Secrets 확인
- Cloud Run 배포 시 `--set-env-vars` 또는 `--update-secrets` 확인
- Secret Manager 권한 확인

## 📚 참고 자료

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [GitHub Actions - Deploy to Cloud Run](https://github.com/google-github-actions/deploy-cloudrun)
- [Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Cloud Run - Environment Variables](https://cloud.google.com/run/docs/configuring/environment-variables)
- [Cloud Run - Secrets](https://cloud.google.com/run/docs/configuring/secrets)

## 🚀 다음 단계

이 이슈가 완료되면:
- [ ] 모니터링 설정 (Cloud Logging, Error Reporting)
- [ ] 알림 설정 (배포 실패 시 Slack/이메일 알림)
- [ ] 롤백 전략 수립
- [ ] 다중 환경 배포 (dev, staging, production)
- [ ] Canary 배포 구현
- [ ] 성능 모니터링 대시보드 구축

---

**브랜치**: `feature/issue-8-cicd-cloud-run` (예정)
**작성자**: Claude
**마지막 업데이트**: 2026-01-24 (계획)
