from typing import Optional
from google.cloud import firestore
from fastapi import HTTPException, status
from datetime import datetime

from app.db.models import User
from app.schemas.user import UserCreate, UserLogin
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)


class AuthService:
    """인증 서비스 (Firestore 기반)"""

    def __init__(self, db: firestore.Client):
        self.db = db
        self.users_collection = db.collection("users")

    def create_user(self, user_data: UserCreate) -> User:
        """
        회원가입

        Args:
            user_data: 사용자 등록 정보

        Returns:
            User: 생성된 사용자 객체

        Raises:
            HTTPException: 이메일 중복 시 400 에러
        """
        # 이메일 중복 체크
        user_doc = self.users_collection.document(user_data.email).get()

        if user_doc.exists:
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
            auth_provider="email",
            created_at=datetime.utcnow(),
            is_active=True
        )

        # Firestore에 저장 (document ID = email)
        self.users_collection.document(user_data.email).set(user.to_dict())

        return user

    def authenticate_user(self, login_data: UserLogin) -> User:
        """
        로그인 인증

        Args:
            login_data: 로그인 정보 (email, password)

        Returns:
            User: 인증된 사용자 객체

        Raises:
            HTTPException: 인증 실패 시 401 또는 403 에러
        """
        # Firestore에서 사용자 조회
        user_doc = self.users_collection.document(login_data.email).get()

        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Firestore 데이터를 User 객체로 변환
        user = User.from_dict(user_doc.to_dict())

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

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        이메일로 사용자 조회

        Args:
            email: 사용자 이메일

        Returns:
            Optional[User]: 사용자 객체 또는 None
        """
        user_doc = self.users_collection.document(email).get()

        if not user_doc.exists:
            return None

        return User.from_dict(user_doc.to_dict())

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        ID로 사용자 조회

        Note: Firestore에서는 email을 document ID로 사용하므로,
        이 메서드는 더 이상 필요하지 않을 수 있습니다.
        기존 호환성을 위해 남겨두지만, get_user_by_email 사용을 권장합니다.

        Args:
            user_id: 사용자 ID (사용 안 함)

        Returns:
            None (Deprecated)
        """
        # Firestore에서는 email을 primary key로 사용하므로
        # 이 메서드는 사용하지 않습니다
        return None
