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
    """User 응답 (비밀번호 제외)

    Note: Firestore에서는 email을 document ID로 사용하므로 id 필드 없음
    """
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
