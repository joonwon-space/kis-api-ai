# Issue #10: 사용자 모델(User) 및 JWT 기반 자체 로그인 구현

**날짜**: 2026-01-27
**이슈 번호**: #10
**상태**: ✅ 구현 완료

## 📋 요약

다중 사용자 지원 및 개인화된 서비스를 위해 회원가입/로그인 시스템을 구축합니다. JWT(Access Token) 방식을 사용하며, 비밀번호는 bcrypt로 Hash 처리하여 저장합니다. 추후 Google Login 등 소셜 로그인 확장이 가능하도록 AuthProvider 패턴을 고려합니다.

## 🎯 목표

1. SQLModel 기반 User 모델 정의 및 DB 설정 (SQLite + Alembic)
2. 비밀번호 해싱 및 JWT 토큰 발급/검증 로직 구현
3. 회원가입/로그인 API 엔드포인트 구현
4. JWT 기반 인증 미들웨어 및 Protected Route 구현
5. 추후 소셜 로그인 확장을 위한 AuthProvider 패턴 설계

## 📐 현재 상태 확인

### 기존 프로젝트 구조
```
kis_api_backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── account.py
│   │           ├── stock.py
│   │           └── balance.py
│   ├── clients/
│   │   └── kis_client.py
│   ├── services/
│   ├── schemas/
│   └── core/
│       ├── config.py
│       └── __init__.py
├── requirements.txt
└── .env
```

### 필요한 새 디렉토리 및 파일
```
kis_api_backend/
├── app/
│   ├── db/                    # 신규
│   │   ├── __init__.py
│   │   ├── database.py        # DB 세션 관리
│   │   └── models.py          # User 모델
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── auth.py    # 신규
│   ├── services/
│   │   └── auth_service.py    # 신규
│   ├── schemas/
│   │   └── user.py            # 신규
│   └── core/
│       ├── security.py        # 신규
│       └── deps.py            # 신규 (의존성 주입)
├── alembic/                   # 신규
│   ├── versions/
│   └── env.py
├── alembic.ini                # 신규
└── kis_api.db                 # 신규 (SQLite DB 파일)
```

## 📐 구현 계획

### 1단계: 의존성 패키지 추가

**requirements.txt 업데이트**:
```txt
# 기존 패키지...

# Database
sqlmodel==0.0.22
alembic==1.13.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

**설치 명령**:
```bash
cd kis_api_backend
pip install sqlmodel alembic python-jose[cryptography] passlib[bcrypt] python-multipart
```

### 2단계: User 모델 정의

**app/db/models.py**:
```python
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """사용자 모델"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # 추후 확장 가능 필드
    full_name: Optional[str] = Field(default=None, max_length=100)
    auth_provider: str = Field(default="email", max_length=50)  # "email", "google", etc.
```

**설계 이유**:
- `email`을 ID로 사용 (unique + index)
- `auth_provider` 필드로 추후 소셜 로그인 구분 가능
- `is_active`로 사용자 비활성화 지원
- `created_at`, `updated_at`으로 감사 추적 가능

### 3단계: DB 세션 관리

**app/db/database.py**:
```python
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///./kis_api.db"

# SQLite 설정 (개발용)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def create_db_and_tables():
    """DB 및 테이블 초기화"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """DB 세션 의존성"""
    with Session(engine) as session:
        yield session
```

**app/db/__init__.py**:
```python
from app.db.database import create_db_and_tables, get_session
from app.db.models import User

__all__ = ["create_db_and_tables", "get_session", "User"]
```

### 4단계: 보안 유틸리티 구현

**app/core/security.py**:
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
SECRET_KEY = "your-secret-key-change-this-in-production"  # TODO: .env로 이동
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWT Access Token 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """JWT Access Token 검증 및 디코딩"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

**보안 주의사항**:
- `SECRET_KEY`는 반드시 `.env`로 이동 (프로덕션 배포 전)
- 최소 32자 이상의 랜덤 문자열 사용
- `ACCESS_TOKEN_EXPIRE_MINUTES`는 보안 정책에 따라 조정

### 5단계: Pydantic 스키마 정의

**app/schemas/user.py**:
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """User 기본 스키마"""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """회원가입 요청"""
    password: str


class UserResponse(UserBase):
    """User 응답 (비밀번호 제외)"""
    id: int
    is_active: bool
    created_at: datetime
    auth_provider: str

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT 토큰 응답"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """토큰 페이로드"""
    user_id: Optional[int] = None
    email: Optional[str] = None
```

### 6단계: Auth 서비스 구현

**app/services/auth_service.py**:
```python
from typing import Optional
from sqlmodel import Session, select
from fastapi import HTTPException, status

from app.db.models import User
from app.schemas.user import UserCreate, UserLogin
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)


class AuthService:
    """인증 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: UserCreate) -> User:
        """회원가입"""
        # 이메일 중복 체크
        existing_user = self.db.exec(
            select(User).where(User.email == user_data.email)
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다."
            )

        # 비밀번호 해싱
        hashed_password = get_password_hash(user_data.password)

        # User 생성
        user = User(
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name,
            auth_provider="email"
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def authenticate_user(self, login_data: UserLogin) -> User:
        """로그인 인증"""
        user = self.db.exec(
            select(User).where(User.email == login_data.email)
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 계정입니다."
            )

        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        return self.db.get(User, user_id)
```

### 7단계: 의존성 주입 (Protected Route)

**app/core/deps.py**:
```python
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from app.db.database import get_session
from app.db.models import User
from app.core.security import decode_access_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
) -> User:
    """현재 로그인한 사용자 가져오기 (Protected Route용)"""
    token = credentials.credentials

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에 사용자 정보가 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다."
        )

    return user
```

### 8단계: Auth API 엔드포인트 구현

**app/api/v1/endpoints/auth.py**:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.database import get_session
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.core.security import create_access_token
from app.core.deps import get_current_user
from app.db.models import User

router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(
    user_data: UserCreate,
    db: Session = Depends(get_session)
):
    """
    회원가입

    - **email**: 이메일 주소 (ID로 사용)
    - **password**: 비밀번호 (최소 8자 권장)
    - **full_name**: 이름 (선택)
    """
    auth_service = AuthService(db)
    user = auth_service.create_user(user_data)
    return user


@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_session)
):
    """
    로그인

    이메일과 비밀번호로 로그인하여 JWT Access Token을 발급받습니다.

    - **email**: 이메일 주소
    - **password**: 비밀번호

    Returns:
        JWT Access Token (30분 유효)
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(login_data)

    # JWT 토큰 생성
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email}
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    현재 로그인한 사용자 정보 조회 (Protected Route 예시)

    Authorization 헤더에 Bearer 토큰이 필요합니다.
    """
    return current_user
```

### 9단계: 라우터 등록

**app/api/v1/api.py 수정**:
```python
from fastapi import APIRouter
from app.api.v1.endpoints import account, stock, balance, auth  # auth 추가

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    account.router,
    prefix="/account",
    tags=["Account"]
)

# 기타 라우터...
```

### 10단계: main.py에 DB 초기화 추가

**app/main.py 수정**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.db.database import create_db_and_tables  # 추가

app = FastAPI(
    title="KIS API Backend",
    description="한국투자증권 Open API를 위한 FastAPI 백엔드",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """앱 시작 시 DB 초기화"""
    create_db_and_tables()


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(api_router, prefix="/api/v1")
```

### 11단계: Alembic 설정 (선택적, 프로덕션용)

**Alembic 초기화**:
```bash
cd kis_api_backend
alembic init alembic
```

**alembic.ini 수정**:
```ini
sqlalchemy.url = sqlite:///./kis_api.db
```

**alembic/env.py 수정**:
```python
from app.db.models import SQLModel

target_metadata = SQLModel.metadata
```

**첫 마이그레이션 생성**:
```bash
alembic revision --autogenerate -m "Create users table"
alembic upgrade head
```

## 🔑 핵심 설계 결정

### 1. SQLite vs PostgreSQL

| 항목 | SQLite | PostgreSQL |
|------|--------|-----------|
| 설정 복잡도 | 쉬움 ✅ | 복잡 |
| 동시성 | 제한적 | 우수 |
| 프로덕션 준비도 | 낮음 | 높음 |
| 초기 개발 속도 | 빠름 ✅ | 느림 |

**결정**: SQLite로 시작 (향후 PostgreSQL 전환 고려)

**이유**:
- 설정 없이 바로 사용 가능
- 로컬 개발 및 테스트에 적합
- SQLModel 덕분에 추후 전환 용이

### 2. bcrypt vs Argon2

| 항목 | bcrypt | Argon2 |
|------|--------|--------|
| 보안 | 높음 | 매우 높음 |
| 속도 | 적절 ✅ | 느림 |
| 라이브러리 지원 | 우수 ✅ | 보통 |
| 표준 지원 | OWASP 권장 ✅ | 최신 표준 |

**결정**: bcrypt 사용

**이유**:
- OWASP 권장 알고리즘
- passlib 라이브러리와 완벽 호환
- 충분한 보안 수준

### 3. JWT Storage

**옵션**:
1. LocalStorage (XSS 취약)
2. Cookie (HttpOnly) ✅
3. Memory (새로고침 시 로그아웃)

**권장**: HttpOnly Cookie (프론트엔드 요구사항에 따라)

**현재 구현**: 프론트엔드가 Access Token을 직접 관리
- API는 토큰만 반환
- 저장 방식은 프론트엔드 결정

### 4. AuthProvider 패턴 (확장성)

**설계 원칙**:
- `auth_provider` 필드로 로그인 방법 구분
- 추후 `GoogleAuthProvider`, `KakaoAuthProvider` 추가 가능

**예시**:
```python
class AuthProvider:
    """인증 제공자 추상 클래스"""

    def authenticate(self, credentials):
        raise NotImplementedError


class EmailAuthProvider(AuthProvider):
    """이메일 인증 (현재 구현)"""

    def authenticate(self, credentials):
        # 현재 로직


class GoogleAuthProvider(AuthProvider):
    """Google OAuth (추후 구현)"""

    def authenticate(self, credentials):
        # Google OAuth 로직
```

## 📋 구현 체크리스트

### 패키지 설치
- [ ] sqlmodel 설치
- [ ] alembic 설치
- [ ] python-jose 설치
- [ ] passlib 설치

### 파일 생성
- [ ] `app/db/__init__.py`
- [ ] `app/db/database.py`
- [ ] `app/db/models.py`
- [ ] `app/core/security.py`
- [ ] `app/core/deps.py`
- [ ] `app/schemas/user.py`
- [ ] `app/services/auth_service.py`
- [ ] `app/api/v1/endpoints/auth.py`

### 기존 파일 수정
- [ ] `app/main.py` (DB 초기화 추가)
- [ ] `app/api/v1/api.py` (auth 라우터 등록)
- [ ] `requirements.txt` (패키지 추가)

### 환경 변수 추가
- [ ] `.env`에 `SECRET_KEY` 추가
- [ ] `.env`에 `ACCESS_TOKEN_EXPIRE_MINUTES` 추가

### 테스트
- [ ] 회원가입 API 테스트
- [ ] 로그인 API 테스트
- [ ] JWT 토큰 검증 테스트
- [ ] Protected Route 테스트 (401 에러)

## ✅ 완료 조건

1. ✅ 회원가입 후 로그인 시 JWT 토큰이 정상 발급되어야 함
   - `POST /api/v1/auth/signup` → 201 Created
   - `POST /api/v1/auth/login` → `{"access_token": "...", "token_type": "bearer"}`

2. ✅ 보호된 라우트에 토큰 없이 접근 시 401 에러 발생
   - `GET /api/v1/auth/me` (토큰 없음) → 401 Unauthorized
   - `GET /api/v1/auth/me` (유효한 토큰) → User 정보 반환

3. ✅ 추후 Google Login 등 확장 가능하도록 설계
   - `auth_provider` 필드로 구분 가능
   - AuthProvider 패턴 고려

## 🧪 테스트 계획

### 1. 회원가입 테스트

**요청**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123",
    "full_name": "홍길동"
  }'
```

**기대 응답** (201 Created):
```json
{
  "id": 1,
  "email": "test@example.com",
  "full_name": "홍길동",
  "is_active": true,
  "auth_provider": "email",
  "created_at": "2026-01-27T10:00:00"
}
```

### 2. 로그인 테스트

**요청**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

**기대 응답** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Protected Route 테스트

**요청 (토큰 없음)**:
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me"
```

**기대 응답** (401 Unauthorized):
```json
{
  "detail": "Not authenticated"
}
```

**요청 (토큰 있음)**:
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**기대 응답** (200 OK):
```json
{
  "id": 1,
  "email": "test@example.com",
  "full_name": "홍길동",
  "is_active": true,
  "auth_provider": "email",
  "created_at": "2026-01-27T10:00:00"
}
```

### 4. 중복 이메일 테스트

**요청** (이미 존재하는 이메일):
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "anotherpassword"
  }'
```

**기대 응답** (400 Bad Request):
```json
{
  "detail": "이미 등록된 이메일입니다."
}
```

### 5. 잘못된 비밀번호 테스트

**요청**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "wrongpassword"
  }'
```

**기대 응답** (401 Unauthorized):
```json
{
  "detail": "이메일 또는 비밀번호가 올바르지 않습니다."
}
```

## 🔍 보안 고려사항

### 1. 비밀번호 정책
- [ ] 최소 8자 이상 (프론트엔드 검증 권장)
- [ ] 영문 + 숫자 + 특수문자 조합 (선택적)
- [ ] 비밀번호 재설정 기능 (추후 구현)

### 2. JWT 토큰 관리
- [ ] `SECRET_KEY`를 `.env`로 이동 (절대 하드코딩 금지)
- [ ] Access Token 만료 시간: 30분 (조정 가능)
- [ ] Refresh Token (추후 구현 고려)

### 3. Rate Limiting
- [ ] 로그인 시도 횟수 제한 (추후 구현)
- [ ] IP 기반 Throttling (선택적)

### 4. HTTPS
- [ ] 프로덕션 배포 시 반드시 HTTPS 사용
- [ ] HTTP에서는 민감 정보 전송 금지

## 📚 참고 자료

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Passlib Documentation](https://passlib.readthedocs.io/)
- [Python-JOSE Documentation](https://python-jose.readthedocs.io/)
- [JWT.io](https://jwt.io/)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

## 🚀 다음 단계 (향후 확장)

이 이슈가 완료되면:
- [ ] Refresh Token 구현
- [ ] 비밀번호 재설정 기능 (이메일 인증)
- [ ] Google OAuth 2.0 로그인 추가
- [ ] 카카오 로그인 추가
- [ ] 사용자 프로필 관리 API
- [ ] 계정 비활성화/삭제 기능
- [ ] 다중 계정 관리 (User-KIS Account 연결)

---

## 📊 구현 완료 (Implementation Completed)

### 구현 내용

#### 1. 파일 구조
```
kis_api_backend/
├── app/
│   ├── db/
│   │   ├── __init__.py          ✅ 신규
│   │   ├── database.py          ✅ 신규
│   │   └── models.py            ✅ 신규 (User 모델)
│   ├── core/
│   │   ├── security.py          ✅ 신규
│   │   └── deps.py              ✅ 신규
│   ├── schemas/
│   │   └── user.py              ✅ 신규
│   ├── services/
│   │   └── auth_service.py      ✅ 신규
│   ├── api/v1/endpoints/
│   │   └── auth.py              ✅ 신규
│   ├── config.py                ✅ 수정 (JWT 설정 추가)
│   └── main.py                  ✅ 수정 (DB 초기화 + 라우터 등록)
├── requirements.txt             ✅ 수정
├── .env                         ✅ 수정 (SECRET_KEY 추가)
└── kis_api.db                   ✅ 자동 생성 (SQLite)
```

#### 2. 설치된 패키지
- `sqlmodel==0.0.31` - SQLAlchemy 기반 ORM
- `alembic==1.18.1` - DB 마이그레이션 도구
- `python-jose==3.5.0` - JWT 토큰 처리
- `passlib==1.7.4` - 비밀번호 해싱
- `bcrypt==4.0.1` - bcrypt 해싱 알고리즘
- `python-multipart==0.0.22` - 파일 업로드 지원
- `email-validator==2.3.0` - 이메일 유효성 검증

#### 3. API 엔드포인트
✅ `POST /api/v1/auth/signup` - 회원가입
✅ `POST /api/v1/auth/login` - 로그인 (JWT 반환)
✅ `GET /api/v1/auth/me` - 현재 사용자 정보 (Protected Route)

#### 4. 테스트 결과

**1. 회원가입 성공**
```json
{
  "email": "test@example.com",
  "full_name": "홍길동",
  "id": 1,
  "is_active": true,
  "created_at": "2026-01-27T12:22:55.117120",
  "auth_provider": "email"
}
```

**2. 로그인 성공 (JWT 토큰 발급)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**3. Protected Route (토큰 있음)**
```json
{
  "email": "test@example.com",
  "full_name": "홍길동",
  "id": 1,
  "is_active": true,
  "created_at": "2026-01-27T12:22:55.117120",
  "auth_provider": "email"
}
```

**4. Protected Route (토큰 없음 - 401)**
```json
{
  "detail": "Not authenticated"
}
```

**5. 중복 회원가입 (400)**
```json
{
  "detail": "이미 등록된 이메일입니다."
}
```

**6. 잘못된 비밀번호 (401)**
```json
{
  "detail": "이메일 또는 비밀번호가 올바르지 않습니다."
}
```

### 구현 특징
1. ✅ **SQLite DB 자동 생성** - 앱 시작 시 자동으로 테이블 생성
2. ✅ **비밀번호 bcrypt 해싱** - 평문 저장 없음
3. ✅ **JWT 토큰 인증** - 30분 만료 시간
4. ✅ **Protected Route 구현** - `get_current_user` 의존성 주입
5. ✅ **확장 가능한 구조** - `auth_provider` 필드로 소셜 로그인 준비

### 보안 고려사항
- ✅ SECRET_KEY는 `.env`에서 관리
- ✅ 비밀번호는 bcrypt로 해싱 (평문 저장 금지)
- ✅ JWT 토큰 30분 만료
- ✅ 이메일 유효성 검증
- ✅ 중복 이메일 방지

---

**브랜치**: `feature/issue-10-user-auth-jwt`
**작성자**: Claude Code
**마지막 업데이트**: 2026-01-27 (구현 완료)
