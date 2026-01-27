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
