# 2026-02-04 Devlog #5: Firestore 마이그레이션

## [작업 시작] Issue #20 - SQLite → Firestore 마이그레이션

### 요청 사항
- SQLite를 버리고 Google Firestore로 완전 마이그레이션
- Cloud Run 재시작 시 데이터 손실 문제 해결
- 영구적인 데이터 저장소 확보

### 구현 계획

#### Phase 1: Firestore 설정 및 기본 구조
- [ ] **의존성 추가**
  - `requirements.txt`에 `google-cloud-firestore` 추가
  - 기존 SQLModel/SQLAlchemy 의존성 유지 (단계적 제거)

- [ ] **Firestore 클라이언트 초기화**
  - `app/db/firestore.py` 생성
  - Singleton 패턴으로 Firestore client 관리
  - 환경변수로 GCP_PROJECT_ID 설정

- [ ] **컬렉션 구조 설계**
  - `users` 컬렉션: document ID = email
  - `daily_assets` 컬렉션: document ID = user_id + snapshot_date 조합
  - `user_settings` 서브컬렉션: users/{email}/settings/{key}

#### Phase 2: User 모델 마이그레이션
- [ ] **User 모델 변환**
  - SQLModel 유지하되 Firestore dict 변환 메서드 추가
  - `to_dict()`, `from_dict()` 메서드 구현
  - Pydantic 검증은 유지

- [ ] **AuthService 수정**
  - 회원가입: `db.collection('users').document(email).set(user_dict)`
  - 로그인 확인: `db.collection('users').document(email).get()`
  - 비밀번호 검증 로직 유지

#### Phase 3: User Settings 마이그레이션
- [ ] **UserSettings 서비스 수정**
  - KIS API 키 저장: `users/{email}/settings/kis_credentials`
  - 암호화된 키 Firestore 저장
  - 조회/업데이트 로직 변경

#### Phase 4: DailyAsset 스냅샷 마이그레이션
- [ ] **DailyAsset 저장 구조 변경**
  - Document ID: `{user_email}_{YYYY-MM-DD}`
  - AssetSnapshotService Firestore 쿼리로 변경
  - 날짜 범위 쿼리: `where('snapshot_date', '>=', start_date)`

#### Phase 5: 배포 및 검증
- [ ] **환경변수 설정**
  - GitHub Secrets에 GCP_PROJECT_ID 추가 (이미 있을 수 있음)
  - deploy.yml에서 Cloud Run에 환경변수 전달

- [ ] **테스트 및 검증**
  - 로컬 테스트 (GCP 인증 필요)
  - 배포 후 회원가입/로그인 테스트
  - 재배포 후 데이터 영속성 확인

### 예상 변경 파일
- `requirements.txt` — google-cloud-firestore 추가
- `app/db/firestore.py` — Firestore 클라이언트 초기화 (신규)
- `app/db/models.py` — to_dict/from_dict 메서드 추가
- `app/services/auth_service.py` — Firestore 쿼리로 변경
- `app/services/user_settings_service.py` — Firestore 저장으로 변경
- `app/services/asset_snapshot_service.py` — Firestore 쿼리로 변경
- `app/services/stats_service.py` — Firestore 집계 쿼리로 변경
- `app/main.py` — Firestore 초기화 추가
- `.github/workflows/deploy.yml` — GCP_PROJECT_ID 환경변수 추가 (필요시)
- `tests/` — 테스트를 Firestore 모킹으로 수정

### 주요 의사결정

#### 1. Document ID 전략
- **Users**: email을 document ID로 사용
  - 장점: 이메일로 직접 접근 가능, 쿼리 불필요
  - 단점: 이메일 변경 시 문제 (이메일 변경 안 한다고 가정)

- **DailyAssets**: `{user_email}_{YYYY-MM-DD}`
  - 장점: 유니크 보장, 날짜별 직접 접근
  - 단점: 범위 쿼리는 별도 필터 필요

#### 2. 단계적 마이그레이션
- SQLModel 코드 즉시 제거하지 않음
- Firestore로 먼저 전환 후 안정화
- 이후 SQLModel/SQLAlchemy 의존성 제거

#### 3. 암호화 키 저장
- 기존 ENCRYPTION_KEY 로직 유지
- Firestore에 암호화된 상태로 저장
- 복호화는 애플리케이션 레벨에서 처리

#### 4. 테스트 전략
- Firestore 에뮬레이터 사용 (로컬 테스트)
- 또는 테스트용 Firestore 프로젝트 사용
- Mock으로 단위 테스트

### 예상 결과
- Cloud Run 재배포 시에도 데이터 유지
- 무료 티어로 운영 가능 (읽기 5만/일, 쓰기 2만/일)
- 스케일링 시 데이터 일관성 보장
- SQLite 파일 의존성 제거

### 리스크/주의사항

#### 데이터 마이그레이션
- 기존 SQLite 데이터는 손실됨 (괜찮음, 테스트 데이터만 있음)
- 프로덕션 데이터 없으므로 마이그레이션 스크립트 불필요

#### 비용
- Firestore 무료 티어 제한 확인 필요
- 초과 시 과금 발생 가능성

#### 성능
- Firestore는 SQLite보다 네트워크 레이턴시 있음
- 하지만 Cloud Run과 같은 리전에 배치하면 최소화

#### 권한
- Cloud Run Service Account에 Firestore 권한 필요
- `roles/datastore.user` 또는 `roles/cloudtasks.enqueuer`

#### 쿼리 제한
- Firestore는 복잡한 조인/집계 쿼리 제한적
- 월별/연도별 통계는 클라이언트 집계 필요할 수 있음

### 1단계 작업 범위 (오늘)
사용자 지시대로 먼저 기본 구조 구축:
1. google-cloud-firestore 패키지 추가
2. app/db/firestore.py 생성 (클라이언트 초기화)
3. User 모델 dict 변환 로직
4. AuthService 적용

나머지는 이후 단계에서 진행.

## [작업 완료] Phase 1: Auth 기본 구조

### 완료된 작업
- [x] **의존성 추가**: requirements.txt에 google-cloud-firestore==2.18.0 추가 및 설치
- [x] **Firestore 클라이언트**: app/db/firestore.py 생성
  - Singleton 패턴으로 클라이언트 관리
  - Project ID: kis-ai-485303
  - ADC(Application Default Credentials) 사용
- [x] **User 모델 변환 메서드**: app/db/models.py 수정
  - `to_dict()`: Firestore 저장용 딕셔너리 변환
  - `from_dict()`: Firestore 데이터를 User 객체로 변환
  - datetime <-> ISO 문자열 변환 처리
- [x] **AuthService 리팩토링**: app/services/auth_service.py
  - Session → firestore.Client 변경
  - 회원가입: `users` 컬렉션에 document ID = email로 저장
  - 로그인: Firestore에서 email로 직접 조회
  - 비밀번호 해싱/검증 로직 유지
- [x] **Auth 엔드포인트 수정**: app/api/v1/endpoints/auth.py
  - get_session → get_firestore_db로 변경
  - JWT 토큰: user_id 제거, email만 사용
- [x] **get_current_user 수정**: app/core/deps.py
  - JWT에서 email 추출
  - Firestore에서 사용자 조회
  - get_kis_client도 user_id → email 변경
- [x] **main.py 초기화**: app/main.py
  - create_db_and_tables() 제거
  - get_firestore_client() 초기화 추가

### 테스트 결과
```bash
$ python -c "from app.db.firestore import get_firestore_client; get_firestore_client()"
Firestore client initialized successfully
```

### 실제 변경 파일
- requirements.txt — google-cloud-firestore 추가
- app/db/firestore.py — Firestore 클라이언트 (신규)
- app/db/models.py — to_dict/from_dict 메서드
- app/services/auth_service.py — Firestore 쿼리로 전환
- app/api/v1/endpoints/auth.py — get_firestore_db 사용
- app/core/deps.py — email 기반 인증으로 변경
- app/main.py — Firestore 초기화

### 남은 작업 (Phase 2-5)

#### Phase 2: UserSettings 마이그레이션 ✅
- [x] UserKeyService Firestore로 변경
- [x] users/{email}/settings/kis_credentials 서브컬렉션 사용
- [x] user_settings.py 엔드포인트 수정

## [Phase 2 완료] UserSettings 마이그레이션

### 완료된 작업
- [x] **UserKeyService 리팩토링**: app/services/user_key_service.py
  - Session → firestore.Client 변경
  - user_id → user_email 변경
  - Firestore 서브컬렉션 사용: `users/{email}/settings/kis_credentials`
  - 암호화 로직 유지
  - create_or_update_user_key: set/update로 전환
  - get_decrypted_keys: email 기반 조회

- [x] **UserSettings 엔드포인트 수정**: app/api/v1/endpoints/user_settings.py
  - get_session → get_firestore_db 변경
  - current_user.id → current_user.email 사용
  - ISO 문자열 → datetime 변환 처리

### Firestore 구조
```
users/{email}/settings (Subcollection)
  └─ kis_credentials (Document)
      ├─ app_key_encrypted: string
      ├─ app_secret_encrypted: string
      ├─ account_no_encrypted: string
      ├─ acnt_prdt_cd_encrypted: string
      ├─ created_at: ISO string
      └─ updated_at: ISO string
```

### 변경 파일
- app/services/user_key_service.py — Firestore 쿼리
- app/api/v1/endpoints/user_settings.py — get_firestore_db 사용

#### Phase 3: DailyAsset 마이그레이션 ✅
- [x] AssetSnapshotService Firestore로 변경
- [x] Document ID: `{email}_{YYYY-MM-DD}`
- [x] dashboard.py 자동 스냅샷 저장 수정

#### Phase 4: StatsService 마이그레이션 ✅
- [x] 일별/월별/연도별 통계 Firestore 쿼리로 변경
- [x] 집계 로직 클라이언트 사이드로 처리

## [Phase 3-4 완료] DailyAsset & Stats 마이그레이션

### Phase 3: DailyAsset 스냅샷
- [x] **AssetSnapshotService 리팩토링**: app/services/asset_snapshot_service.py
  - Session → firestore.Client 변경
  - user_id → user_email 변경
  - Document ID: `{email}_{YYYY-MM-DD}` 형식
  - Firestore 컬렉션: `daily_assets`
  - 날짜 범위 쿼리: where + order_by로 구현

- [x] **Dashboard 엔드포인트 수정**: app/api/v1/endpoints/dashboard.py
  - get_session → get_firestore_db 변경
  - current_user.id → current_user.email 사용

### Phase 4: StatsService
- [x] **StatsService 리팩토링**: app/services/stats_service.py
  - Session → firestore.Client 변경
  - user_id → user_email 변경
  - dict 접근 방식으로 변경 (snapshot["field"])
  - ISO 문자열 → date 변환 처리
  - 클라이언트 사이드 집계 유지

- [x] **Stats 엔드포인트 수정**: app/api/v1/endpoints/stats.py
  - get_session → get_firestore_db 변경
  - current_user.id → current_user.email 사용

### Firestore 구조
```
daily_assets (Collection)
  └─ {email}_{YYYY-MM-DD} (Document)
      ├─ user_email: string
      ├─ snapshot_date: string (YYYY-MM-DD)
      ├─ total_asset: float
      ├─ total_purchase_amount: float
      ├─ total_profit_loss: float
      ├─ profit_loss_rate: float
      ├─ deposit: float
      ├─ stock_evaluation: float
      └─ created_at: ISO string
```

### 변경 파일 (Phase 3-4)
- app/services/asset_snapshot_service.py — Firestore 쿼리
- app/services/stats_service.py — Firestore 쿼리
- app/api/v1/endpoints/dashboard.py — get_firestore_db 사용
- app/api/v1/endpoints/stats.py — get_firestore_db 사용

#### Phase 5: 배포 및 검증
- [ ] 로컬 테스트 (회원가입/로그인/통계)
- [ ] Cloud Run Service Account 권한 확인
- [ ] deploy.yml에서 GCP_PROJECT_ID 환경변수 확인
- [ ] 배포 및 데이터 영속성 검증
- [ ] 재배포 후 데이터 유지 확인

### 다음 스텝
UserKeyService를 Firestore로 마이그레이션하여 API 키 저장/조회 기능 복원
