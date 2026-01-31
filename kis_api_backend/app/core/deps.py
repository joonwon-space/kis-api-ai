import sys
from pathlib import Path
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

# Add parent directory to path to import kis_client
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.db.database import get_session
from app.db.models import User
from app.core.security import decode_access_token
from app.services.user_key_service import UserKeyService
from app.config import settings
from kis_client import KISClient

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


def get_kis_client(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> KISClient:
    """현재 사용자의 KIS 클라이언트 반환

    사용자의 등록된 API 키를 복호화하여 KIS Client를 동적으로 생성합니다.

    Args:
        current_user: 현재 로그인한 사용자
        session: DB 세션

    Returns:
        KISClient: 사용자별 KIS API 클라이언트

    Raises:
        HTTPException: API 키가 등록되지 않은 경우 400 에러
    """
    service = UserKeyService(session)
    keys = service.get_decrypted_keys(current_user.id)

    if not keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="증권사 API 키가 등록되지 않았습니다. POST /api/v1/user/settings 에서 먼저 등록하세요."
        )

    # 사용자별 KIS Client 생성
    return KISClient(
        app_key=keys.app_key,
        app_secret=keys.app_secret,
        account_no=keys.account_no,
        acnt_prdt_cd=keys.acnt_prdt_cd,
        is_simulation=settings.is_simulation
    )
