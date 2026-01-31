# 2026-01-31-01: 사용자별 증권사 API Key 암호화 저장 및 관리 기능

**작성일:** 2026-01-31
**관련 Issue:** #11
**작업자:** Claude Code

---

## 📋 작업 개요

### 목적
사용자마다 다른 증권사 계좌를 사용하므로, 로그인한 사용자의 **KIS API Key, Secret, 계좌번호**를 DB에 암호화하여 안전하게 저장하고 관리하는 기능을 구현합니다.

### 현재 상황 분석
현재 시스템의 문제점:
- `config.py`에서 환경변수로부터 전역 KIS API 설정을 로드 (모든 사용자가 공유)
- 다중 사용자 환경에서 각자의 증권 계좌를 사용할 수 없음
- API Key가 평문으로 환경변수에 저장되어 보안 취약

**필요한 개선:**
1. 사용자별 KIS API 정보 저장
2. DB 저장 시 암호화 (cryptography의 Fernet)
3. 복호화는 런타임에만 메모리에서 수행

---

## 🎯 요구사항 분석

### 기능 요구사항
1. **암호화/복호화 유틸리티**
   - `cryptography` 라이브러리의 Fernet 사용
   - 암호화 키는 환경변수(`ENCRYPTION_KEY`)로 관리
   - 양방향 암호화로 API 호출 시 복호화 가능

2. **UserKey 모델**
   - User와 1:1 관계
   - 필드: `app_key`, `app_secret`, `account_no`, `acnt_prdt_cd` (모두 암호화)
   - DB에는 암호문으로 저장

3. **API 엔드포인트**
   - `GET /api/v1/user/settings`: 키 정보 조회 (마스킹 처리)
   - `POST /api/v1/user/settings`: 키 등록 및 수정

### 보안 요구사항
1. DB 파일을 열었을 때 평문 노출 금지
2. 로그에 민감 정보 출력 금지
3. API 응답 시 마스킹 처리 (예: `****1234`)
4. 암호화 키는 반드시 환경변수로 관리

### 완료 조건
- [ ] `.sqlite` 파일 내 API Key/Secret이 암호문으로 저장됨
- [ ] API를 통해 정상적으로 키 저장 및 조회 가능
- [ ] GET 응답 시 마스킹 처리 확인
- [ ] pytest 테스트 통과

---

## 📐 설계 및 구현 계획

### 1단계: 암호화 유틸리티 구현
**파일:** `app/core/encryption.py`

```python
from cryptography.fernet import Fernet
from app.config import settings

class EncryptionService:
    """Fernet 기반 암호화/복호화 서비스"""

    def __init__(self):
        # ENCRYPTION_KEY는 환경변수에서 로드
        self.cipher = Fernet(settings.encryption_key.encode())

    def encrypt(self, plain_text: str) -> str:
        """평문을 암호화하여 문자열로 반환"""
        return self.cipher.encrypt(plain_text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        """암호문을 복호화하여 평문 반환"""
        return self.cipher.decrypt(encrypted_text.encode()).decode()
```

**주요 결정:**
- Fernet은 대칭키 암호화로 간단하고 안전
- 암호화 키는 32바이트 URL-safe base64 인코딩 문자열 (`Fernet.generate_key()`)
- 환경변수에 저장하여 코드와 분리

---

### 2단계: UserKey 모델 추가
**파일:** `app/db/models.py`

```python
class UserKey(SQLModel, table=True):
    """사용자별 증권사 API 키 (암호화 저장)"""
    __tablename__ = "user_keys"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)

    # 암호화된 필드
    app_key_encrypted: str = Field(max_length=500)
    app_secret_encrypted: str = Field(max_length=500)
    account_no_encrypted: str = Field(max_length=500)
    acnt_prdt_cd_encrypted: str = Field(max_length=500)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
```

**주요 결정:**
- `user_id`에 unique 제약으로 1:1 관계 보장
- 컬럼명에 `_encrypted` 접미사로 암호화 필드임을 명시
- max_length=500: Fernet 암호문은 평문보다 길어짐 (base64 인코딩)

---

### 3단계: Pydantic 스키마 추가
**파일:** `app/schemas/user_key.py`

```python
class UserKeyCreate(BaseModel):
    """키 등록 요청 (평문)"""
    app_key: str
    app_secret: str
    account_no: str
    acnt_prdt_cd: str

class UserKeyResponse(BaseModel):
    """키 조회 응답 (마스킹)"""
    app_key_masked: str  # "****1234"
    app_secret_masked: str
    account_no_masked: str
    acnt_prdt_cd: str  # 상품코드는 민감하지 않으므로 평문
    created_at: datetime
    updated_at: Optional[datetime]
```

**마스킹 로직:**
- 앞 4자 제외, 나머지 `*` 처리
- 뒤 4자만 표시: `f"****{value[-4:]}"`

---

### 4단계: UserKey Service 구현
**파일:** `app/services/user_key_service.py`

```python
from app.core.encryption import EncryptionService
from app.db.models import UserKey
from sqlmodel import Session

class UserKeyService:
    def __init__(self, session: Session):
        self.session = session
        self.encryption = EncryptionService()

    def create_or_update_user_key(self, user_id: int, data: UserKeyCreate) -> UserKey:
        """사용자 키 생성 또는 업데이트"""
        # 기존 키 확인
        user_key = self.session.query(UserKey).filter(UserKey.user_id == user_id).first()

        if user_key:
            # 업데이트
            user_key.app_key_encrypted = self.encryption.encrypt(data.app_key)
            user_key.app_secret_encrypted = self.encryption.encrypt(data.app_secret)
            user_key.account_no_encrypted = self.encryption.encrypt(data.account_no)
            user_key.acnt_prdt_cd_encrypted = self.encryption.encrypt(data.acnt_prdt_cd)
            user_key.updated_at = datetime.utcnow()
        else:
            # 생성
            user_key = UserKey(
                user_id=user_id,
                app_key_encrypted=self.encryption.encrypt(data.app_key),
                app_secret_encrypted=self.encryption.encrypt(data.app_secret),
                account_no_encrypted=self.encryption.encrypt(data.account_no),
                acnt_prdt_cd_encrypted=self.encryption.encrypt(data.acnt_prdt_cd)
            )
            self.session.add(user_key)

        self.session.commit()
        self.session.refresh(user_key)
        return user_key

    def get_user_key(self, user_id: int) -> Optional[UserKey]:
        """사용자 키 조회"""
        return self.session.query(UserKey).filter(UserKey.user_id == user_id).first()

    def get_decrypted_keys(self, user_id: int) -> Optional[dict]:
        """복호화된 키 반환 (KIS API 호출용)"""
        user_key = self.get_user_key(user_id)
        if not user_key:
            return None

        return {
            "app_key": self.encryption.decrypt(user_key.app_key_encrypted),
            "app_secret": self.encryption.decrypt(user_key.app_secret_encrypted),
            "account_no": self.encryption.decrypt(user_key.account_no_encrypted),
            "acnt_prdt_cd": self.encryption.decrypt(user_key.acnt_prdt_cd_encrypted)
        }

    def mask_value(self, value: str) -> str:
        """마스킹 처리 (뒤 4자만 표시)"""
        if len(value) <= 4:
            return "****"
        return f"****{value[-4:]}"
```

---

### 5단계: API 엔드포인트 구현
**파일:** `app/api/v1/endpoints/user_settings.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.db.database import get_session
from app.core.deps import get_current_user
from app.db.models import User
from app.schemas.user_key import UserKeyCreate, UserKeyResponse
from app.services.user_key_service import UserKeyService

router = APIRouter(prefix="/user/settings", tags=["User Settings"])

@router.post("", response_model=UserKeyResponse, status_code=201)
def register_user_keys(
    data: UserKeyCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """사용자 API 키 등록 및 수정"""
    service = UserKeyService(session)
    user_key = service.create_or_update_user_key(current_user.id, data)

    # 마스킹 처리 후 반환
    return UserKeyResponse(
        app_key_masked=service.mask_value(data.app_key),
        app_secret_masked=service.mask_value(data.app_secret),
        account_no_masked=service.mask_value(data.account_no),
        acnt_prdt_cd=data.acnt_prdt_cd,
        created_at=user_key.created_at,
        updated_at=user_key.updated_at
    )

@router.get("", response_model=UserKeyResponse)
def get_user_keys(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """사용자 API 키 조회 (마스킹)"""
    service = UserKeyService(session)
    user_key = service.get_user_key(current_user.id)

    if not user_key:
        raise HTTPException(status_code=404, detail="등록된 API 키가 없습니다.")

    # 복호화 후 마스킹
    decrypted = service.get_decrypted_keys(current_user.id)

    return UserKeyResponse(
        app_key_masked=service.mask_value(decrypted["app_key"]),
        app_secret_masked=service.mask_value(decrypted["app_secret"]),
        account_no_masked=service.mask_value(decrypted["account_no"]),
        acnt_prdt_cd=decrypted["acnt_prdt_cd"],
        created_at=user_key.created_at,
        updated_at=user_key.updated_at
    )
```

**엔드포인트 등록:**
- `app/api/v1/__init__.py`에 라우터 추가

---

### 6단계: Config 업데이트
**파일:** `app/config.py`

```python
class Settings(BaseSettings):
    # 기존 KIS API 설정 (하위 호환성 유지, Optional로 변경)
    app_key: Optional[str] = Field(default=None, alias="APP_KEY")
    app_secret: Optional[str] = Field(default=None, alias="APP_SECRET")
    account_no: Optional[str] = Field(default=None, alias="ACCOUNT_NO")
    acnt_prdt_cd: Optional[str] = Field(default="01", alias="ACNT_PRDT_CD")

    # 암호화 키 (새로 추가)
    encryption_key: str = Field(..., alias="ENCRYPTION_KEY")

    # JWT Settings
    secret_key: str = Field(...)
    access_token_expire_minutes: int = Field(default=30)
```

**`.env.example` 업데이트:**
```env
# Encryption
ENCRYPTION_KEY=<Fernet.generate_key() 결과>

# KIS API (선택 사항 - 사용자별 키 사용 권장)
APP_KEY=
APP_SECRET=
ACCOUNT_NO=
ACNT_PRDT_CD=01

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

### 7단계: KIS Client 수정
**파일:** `app/clients/kis_client.py`

기존 KIS Client는 전역 config를 사용하므로, 사용자별 키를 받아서 동작하도록 수정:

```python
class KISClient:
    def __init__(self, app_key: str, app_secret: str, account_no: str, acnt_prdt_cd: str):
        """사용자별 KIS 클라이언트 초기화"""
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_no = account_no
        self.acnt_prdt_cd = acnt_prdt_cd
        # ...
```

**의존성 주입 패턴:**
```python
# app/core/deps.py
def get_kis_client(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> KISClient:
    """현재 사용자의 KIS 클라이언트 반환"""
    service = UserKeyService(session)
    keys = service.get_decrypted_keys(current_user.id)

    if not keys:
        raise HTTPException(
            status_code=400,
            detail="증권사 API 키가 등록되지 않았습니다. /api/v1/user/settings에서 먼저 등록하세요."
        )

    return KISClient(**keys)
```

---

## 🧪 테스트 전략

### 단위 테스트
**파일:** `tests/test_encryption.py`
```python
def test_encryption_decryption():
    """암호화/복호화 정상 동작 확인"""
    service = EncryptionService()
    plain = "test_app_key_1234"
    encrypted = service.encrypt(plain)

    assert encrypted != plain
    assert service.decrypt(encrypted) == plain

def test_encrypted_value_is_not_readable():
    """암호화된 값이 평문과 전혀 다름을 확인"""
    service = EncryptionService()
    plain = "my_secret_key"
    encrypted = service.encrypt(plain)

    assert plain not in encrypted
```

**파일:** `tests/test_user_key_service.py`
```python
def test_create_user_key(session):
    """UserKey 생성 테스트"""
    service = UserKeyService(session)
    data = UserKeyCreate(
        app_key="test_key",
        app_secret="test_secret",
        account_no="12345678",
        acnt_prdt_cd="01"
    )

    user_key = service.create_or_update_user_key(user_id=1, data=data)

    # DB에는 암호문으로 저장됨
    assert user_key.app_key_encrypted != "test_key"

    # 복호화하면 원본과 일치
    decrypted = service.get_decrypted_keys(user_id=1)
    assert decrypted["app_key"] == "test_key"

def test_masking():
    """마스킹 로직 테스트"""
    service = UserKeyService(session)
    masked = service.mask_value("ABCDEFGH1234")
    assert masked == "****1234"
```

### 통합 테스트
**파일:** `tests/test_api/test_user_settings.py`
```python
def test_register_user_keys(client, auth_token):
    """API 키 등록 엔드포인트 테스트"""
    response = client.post(
        "/api/v1/user/settings",
        json={
            "app_key": "TEST_APP_KEY_1234",
            "app_secret": "SECRET_5678",
            "account_no": "12345678",
            "acnt_prdt_cd": "01"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["app_key_masked"] == "****1234"
    assert data["app_secret_masked"] == "****5678"

def test_get_user_keys(client, auth_token):
    """API 키 조회 엔드포인트 테스트"""
    # 먼저 등록
    client.post("/api/v1/user/settings", json={...}, headers={...})

    # 조회
    response = client.get(
        "/api/v1/user/settings",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "****" in data["app_key_masked"]
```

### 보안 검증 테스트
```python
def test_db_stores_encrypted_values():
    """DB에 평문이 저장되지 않음을 확인"""
    # SQLite 파일 직접 읽기
    conn = sqlite3.connect("kis_api.db")
    cursor = conn.cursor()
    cursor.execute("SELECT app_key_encrypted FROM user_keys LIMIT 1")
    row = cursor.fetchone()

    # 평문 키가 포함되지 않아야 함
    assert "TEST_APP_KEY" not in row[0]
    conn.close()
```

---

## 📝 Migration 계획

### DB 마이그레이션
1. 기존 사용자는 API 키 미등록 상태
2. `/api/v1/user/settings` POST로 최초 등록 필요
3. 등록 전까지는 KIS API 호출 시 400 에러 반환

### 점진적 적용
1. **Phase 1:** UserKey 모델 및 API 구현 (이번 이슈)
2. **Phase 2:** 기존 엔드포인트들이 `get_kis_client()` 의존성 사용하도록 수정
3. **Phase 3:** 전역 config의 KIS 설정 제거 (환경변수 정리)

---

## 🚨 보안 체크리스트

- [ ] `ENCRYPTION_KEY`가 `.env`에 있고 `.gitignore`에 포함됨
- [ ] `token.json`, `kis_api.db`가 `.gitignore`에 포함됨
- [ ] 로그에 평문 API Key 출력 금지
- [ ] API 응답에서 마스킹 처리 확인
- [ ] pytest로 암호화 검증 테스트 통과
- [ ] SQLite 파일 열어서 암호문 확인

---

## 📦 구현 파일 목록

### 신규 생성
- `app/core/encryption.py` - 암호화 유틸리티
- `app/schemas/user_key.py` - UserKey 스키마
- `app/services/user_key_service.py` - UserKey 비즈니스 로직
- `app/api/v1/endpoints/user_settings.py` - API 엔드포인트
- `tests/test_encryption.py` - 암호화 테스트
- `tests/test_user_key_service.py` - 서비스 테스트
- `tests/test_api/test_user_settings.py` - API 테스트

### 수정
- `app/db/models.py` - UserKey 모델 추가
- `app/config.py` - ENCRYPTION_KEY 추가
- `app/core/deps.py` - get_kis_client() 의존성 추가
- `app/api/v1/__init__.py` - 라우터 등록
- `.env.example` - ENCRYPTION_KEY 예시 추가
- `requirements.txt` - cryptography 추가

---

## 🎯 완료 후 검증

```bash
# 1. 패키지 설치
pip install cryptography

# 2. 암호화 키 생성 및 .env 추가
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 3. DB 초기화 및 테스트 실행
pytest tests/test_encryption.py -v
pytest tests/test_user_key_service.py -v
pytest tests/test_api/test_user_settings.py -v

# 4. 서버 실행 및 수동 테스트
uvicorn app.main:app --reload

# 5. SQLite DB 확인
sqlite3 kis_api.db "SELECT * FROM user_keys;"
# 암호문인지 확인: gAAAAA... 같은 형태여야 함
```

---

**다음 단계:**
- 사용자 승인 후 feature 브랜치 생성
- 단계별 구현 및 커밋
- pytest 테스트 작성 및 검증
- PR 생성 및 리뷰

**예상 커밋 순서:**
1. `feat: 암호화 유틸리티 구현 (EncryptionService)`
2. `feat: UserKey 모델 및 스키마 추가`
3. `feat: UserKeyService 비즈니스 로직 구현`
4. `feat: 사용자 설정 API 엔드포인트 구현`
5. `test: 암호화 및 UserKey 테스트 추가`
6. `docs: .env.example에 ENCRYPTION_KEY 추가`
