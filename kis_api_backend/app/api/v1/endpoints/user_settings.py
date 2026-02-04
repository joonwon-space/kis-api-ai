from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud import firestore
from datetime import datetime
from app.db.firestore import get_firestore_db
from app.core.deps import get_current_user
from app.db.models import User
from app.schemas.user_key import UserKeyCreate, UserKeyResponse
from app.services.user_key_service import UserKeyService

router = APIRouter(prefix="/user/settings", tags=["User Settings"])


@router.post("", response_model=UserKeyResponse, status_code=status.HTTP_201_CREATED)
def register_user_keys(
    data: UserKeyCreate,
    current_user: User = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore_db),
):
    """사용자 증권사 API 키 등록 및 수정

    사용자의 KIS API Key, Secret, 계좌번호를 암호화하여 Firestore에 저장합니다.
    이미 등록된 키가 있으면 업데이트합니다.

    Args:
        data: API 키 정보 (평문)
        current_user: 현재 로그인한 사용자
        db: Firestore 클라이언트

    Returns:
        마스킹 처리된 API 키 정보
    """
    service = UserKeyService(db)
    user_key = service.create_or_update_user_key(current_user.email, data)

    # created_at, updated_at을 datetime 객체로 변환
    created_at = None
    if user_key.get("created_at"):
        created_at = datetime.fromisoformat(user_key["created_at"])

    updated_at = None
    if user_key.get("updated_at"):
        updated_at = datetime.fromisoformat(user_key["updated_at"])

    # 마스킹 처리 후 반환
    return UserKeyResponse(
        app_key_masked=service.mask_value(data.app_key),
        app_secret_masked=service.mask_value(data.app_secret),
        account_no_masked=service.mask_value(data.account_no),
        acnt_prdt_cd=data.acnt_prdt_cd,
        created_at=created_at or datetime.utcnow(),
        updated_at=updated_at,
    )


@router.get("", response_model=UserKeyResponse)
def get_user_keys(
    current_user: User = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore_db),
):
    """사용자 증권사 API 키 조회

    등록된 API 키 정보를 마스킹 처리하여 반환합니다.
    보안을 위해 실제 키 값은 노출하지 않고 일부만 표시합니다.

    Args:
        current_user: 현재 로그인한 사용자
        db: Firestore 클라이언트

    Returns:
        마스킹 처리된 API 키 정보

    Raises:
        HTTPException: 등록된 키가 없는 경우 404
    """
    service = UserKeyService(db)
    user_key = service.get_user_key(current_user.email)

    if not user_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="등록된 API 키가 없습니다. POST /api/v1/user/settings 를 통해 먼저 등록하세요.",
        )

    # 복호화 후 마스킹
    decrypted = service.get_decrypted_keys(current_user.email)

    # created_at, updated_at을 datetime 객체로 변환
    created_at = None
    if user_key.get("created_at"):
        created_at = datetime.fromisoformat(user_key["created_at"])

    updated_at = None
    if user_key.get("updated_at"):
        updated_at = datetime.fromisoformat(user_key["updated_at"])

    return UserKeyResponse(
        app_key_masked=service.mask_value(decrypted.app_key),
        app_secret_masked=service.mask_value(decrypted.app_secret),
        account_no_masked=service.mask_value(decrypted.account_no),
        acnt_prdt_cd=decrypted.acnt_prdt_cd,
        created_at=created_at or datetime.utcnow(),
        updated_at=updated_at,
    )
