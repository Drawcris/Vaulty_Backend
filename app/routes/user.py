"""Routes dla mapowania wallet -> username."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.user_crud import UserCRUD
from app.database import get_db
from app.dependencies import get_current_wallet
from app.schemas.user_schemas import (
    SetUsernameRequest,
    UserResponse,
    WalletLookupResponse,
    UpdatePublicKeyRequest,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    user = UserCRUD.get_by_wallet(db, wallet)

    if not user:
        return UserResponse(wallet=wallet, username=None)

    return user


@router.post("/set-username", response_model=UserResponse)
async def set_username(
    request: SetUsernameRequest,
    wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    existing_user = UserCRUD.get_by_wallet(db, wallet)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already set and cannot be changed"
        )

    if UserCRUD.get_by_username(db, request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    return UserCRUD.create_user(db=db, wallet=wallet, username=request.username, encryption_public_key=request.encryption_public_key)


@router.get("/by-username/{username}", response_model=WalletLookupResponse)
async def get_wallet_by_username(
    username: str,
    db: Session = Depends(get_db)
):
    user = UserCRUD.get_by_username(db, username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return WalletLookupResponse(wallet=user.wallet)


@router.get("/search", response_model=list[UserResponse])
async def search_users(
    q: str,
    db: Session = Depends(get_db)
):
    """Przeszukuje użytkowników po nazwie (autocomplete)"""
    if len(q) < 1:
        return []
    return UserCRUD.search_usernames(db, q)


@router.get("/public-key/{wallet_or_username}")
async def get_user_public_key(
    wallet_or_username: str,
    db: Session = Depends(get_db)
):
    """Pobierz klucz publiczny szyfrowania użytkownika po wallet lub username"""
    from eth_utils import is_address
    if is_address(wallet_or_username):
        user = UserCRUD.get_by_wallet(db, wallet_or_username)
    else:
        user = UserCRUD.get_by_username(db, wallet_or_username)

    if not user or not user.encryption_public_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or encryption key not set"
        )

    return {"wallet": user.wallet, "encryption_public_key": user.encryption_public_key}

@router.put("/public-key", response_model=UserResponse)
async def update_public_key(
    request: UpdatePublicKeyRequest,
    wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    user = UserCRUD.get_by_wallet(db, wallet)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserCRUD.update_public_key(db, user, request.encryption_public_key)
