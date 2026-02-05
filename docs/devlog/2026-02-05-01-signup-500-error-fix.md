# 2026-02-05 Devlog #1: 회원가입 API 500 에러 수정

## [작업 시작] Issue #22 - 회원가입 API 500 에러 해결

### 요청 사항
- Cloud Run 배포 환경에서 `/api/v1/auth/signup` 엔드포인트 호출 시 500 Internal Server Error 발생
- Firestore 마이그레이션 이후 발생한 문제로 추정
- DB 연결 설정, 권한, 환경 변수 등을 점검하여 해결

### 문제 분석

#### 코드 리뷰 결과
1. **Firestore 클라이언트 초기화** (`app/db/firestore.py:28`)
   - 프로젝트 ID가 하드코딩: `project="kis-ai-485303"`
   - 에러 로깅은 있지만 구체적인 원인 파악이 어려움

2. **환경 변수** (`app/config.py:24`)
   - `ENCRYPTION_KEY`가 필수 필드로 설정: `Field(...)`
   - 환경 변수가 없으면 애플리케이션 시작 시 오류 발생

3. **의존성** (`requirements.txt:14`)
   - ✅ `google-cloud-firestore==2.18.0` 포함됨

4. **Dockerfile**
   - ✅ requirements.txt 설치 로직 정상

#### 예상 원인 (우선순위 순)
1. **ENCRYPTION_KEY 환경 변수 누락** (가장 가능성 높음)
   - Config 초기화 시 필수 필드이므로 누락 시 500 에러
   - Cloud Run 환경 변수 설정에서 누락되었을 가능성

2. **Cloud Run Service Account 권한 부족**
   - Firestore 접근을 위한 `roles/datastore.user` 권한 필요
   - Service Account에 권한이 없으면 인증 실패

3. **Firestore API 비활성화**
   - GCP 프로젝트에서 Firestore API가 활성화되지 않았을 수 있음

4. **ADC (Application Default Credentials) 인증 실패**
   - Cloud Run에서 자동으로 Service Account 인증해야 하나 실패할 수 있음

### 구현 계획

#### 1단계: 에러 로깅 개선 ✅
- [x] **Firestore 초기화 로깅 강화** - `app/db/firestore.py`
  - 초기화 시도 시 프로젝트 ID 로그 출력
  - 예외 발생 시 상세 스택 트레이스 포함 (`exc_info=True`)
  - Connection test 로직 추가 (collections 메서드 호출)
  - RuntimeError로 명확한 에러 메시지 전달

- [x] **Config 로딩 로깅 추가** - `app/config.py`
  - ENCRYPTION_KEY 로딩 여부 로그 (값은 마스킹)
  - 환경 변수 누락 시 RuntimeError로 명확한 메시지
  - try-except로 설정 로딩 실패 캡처

- [x] **Auth signup 엔드포인트 에러 핸들링** - `app/api/v1/endpoints/auth.py`
  - try-except로 명확한 에러 메시지 반환
  - 상세 로깅 추가 (`exc_info=True`)
  - HTTPException은 그대로 전달 (이메일 중복 등)

#### 2단계: 환경 변수 설정 확인 ✅
- [x] **deploy.yml 확인** - `.github/workflows/deploy.yml`
  - ✅ ENCRYPTION_KEY 환경 변수 이미 설정됨 (76번 줄)
  - GitHub Secrets에서 전달되고 있음

- [ ] **README/문서 업데이트**
  - 배포 시 필요한 환경 변수 목록 문서화

#### 3단계: Cloud Run 권한 확인
- [ ] **Service Account 권한 체크**
  - Cloud Run Service Account 확인
  - Firestore User 역할 부여 확인
  - 필요 시 `gcloud projects add-iam-policy-binding` 명령 실행

#### 4단계: Firestore API 활성화 확인
- [ ] **GCP Console 확인**
  - Firestore API 활성화 여부 확인
  - Firestore Native 모드 활성화 확인

#### 5단계: 배포 및 검증
- [ ] **코드 수정 후 재배포**
  - Feature 브랜치 생성
  - 수정 사항 커밋
  - PR 생성 및 배포

- [ ] **회원가입 테스트**
  - curl 명령으로 회원가입 API 호출
  - 201 Created 응답 확인
  - Firestore Console에서 users 컬렉션 확인

- [ ] **로그 확인**
  - Cloud Run 로그에서 에러 메시지 확인
  - 필요 시 추가 수정

### 예상 변경 파일
- `app/db/firestore.py` — 로깅 강화, 에러 메시지 개선
- `app/config.py` — ENCRYPTION_KEY 로깅 추가
- `app/api/v1/endpoints/auth.py` — 에러 핸들링 개선
- `.github/workflows/deploy.yml` — ENCRYPTION_KEY 환경 변수 추가 (필요 시)
- `README.md` — 환경 변수 문서화 (필요 시)

### 의사결정

#### 1. 프로젝트 ID 하드코딩 유지
- 현재: `firestore.Client(project="kis-ai-485303")`
- **결정**: 하드코딩 유지
- **이유**: 프로젝트가 하나이고, 환경 변수로 관리해도 이점이 크지 않음
- **대안**: 추후 멀티 프로젝트 지원 시 환경 변수로 변경

#### 2. 에러 로깅 우선
- **결정**: 먼저 로깅을 개선하여 정확한 원인 파악
- **이유**: 로컬에서는 재현되지 않아 배포 환경 로그 필요
- **접근**: 상세한 로깅 → 배포 → 로그 확인 → 수정

#### 3. ENCRYPTION_KEY 환경 변수 추가
- **결정**: GitHub Secrets에 ENCRYPTION_KEY 추가 필수
- **이유**: Config 초기화 시 필수 필드이므로 누락 시 500 에러
- **방법**: GitHub Secrets → deploy.yml에서 전달

### 리스크/주의사항

#### 1. 환경 변수 노출
- ENCRYPTION_KEY를 로그에 출력하지 않도록 주의
- 로깅 시 마스킹 처리

#### 2. Service Account 권한
- 과도한 권한 부여 방지
- `roles/datastore.user`만 부여 (최소 권한 원칙)

#### 3. 재배포 필요
- 환경 변수 추가 시 재배포 필요
- 다운타임 최소화

### 다음 할 일
1. 로깅 개선 코드 작성 ✅
2. 사용자 승인 후 구현 시작 ✅
3. 배포 및 검증

---

## [작업 진행] 에러 로깅 개선 완료

### 완료된 작업
- [x] Feature 브랜치 생성: `feature/issue-22-signup-500-error`
- [x] Firestore 초기화 로깅 강화
  - 프로젝트 ID 로그 출력
  - Connection test 추가
  - 상세 스택 트레이스 (`exc_info=True`)
- [x] Config 로딩 로깅 추가
  - ENCRYPTION_KEY 설정 확인
  - 명확한 에러 메시지
- [x] Auth signup 엔드포인트 에러 핸들링
  - try-except 추가
  - 상세 로깅
- [x] 커밋 및 푸시
- [x] PR 생성: #23

### 변경된 파일
- `kis_api_backend/app/db/firestore.py`
- `kis_api_backend/app/config.py`
- `kis_api_backend/app/api/v1/endpoints/auth.py`
- `docs/devlog/2026-02-05-01-signup-500-error-fix.md`

### 다음 단계
- [ ] PR 머지
- [ ] 자동 배포 대기 (GitHub Actions)
- [ ] Cloud Run 로그 확인
- [ ] 회원가입 API 테스트
- [ ] 에러 원인 파악 및 추가 수정 (필요 시)

---

## [작업 완료] 근본 원인 발견 및 해결

### 배포 과정
- [x] 첫 번째 배포 실패: Config 로딩 시 RuntimeError 발생으로 컨테이너 시작 실패
- [x] Config 로직 복원 및 재배포
- [x] 두 번째 배포 실패: Firestore connection test 타임아웃
- [x] Connection test 제거 및 재배포
- [x] 세 번째 배포 성공! ✅

### 근본 원인 발견
회원가입 API 테스트 결과:
```
404 The database (default) does not exist for project kis-ai-485303
```

**근본 원인**: Firestore 데이터베이스가 GCP 프로젝트에 생성되지 않았음

### 해결 방법
사용자가 `kis-ai-db`라는 이름으로 Firestore 데이터베이스 생성

코드 수정:
- `app/db/firestore.py`에서 데이터베이스 이름 지정: `database="kis-ai-db"`

### 최종 변경 파일
- `kis_api_backend/app/db/firestore.py` — 데이터베이스 이름 추가

### 다음 단계
- [ ] 배포 후 회원가입 API 재테스트
- [ ] Firestore Console에서 users 컬렉션 확인
- [ ] Issue #22 종료
