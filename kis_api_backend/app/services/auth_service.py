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
