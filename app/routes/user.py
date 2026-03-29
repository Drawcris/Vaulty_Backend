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

    return UserCRUD.create_user(db=db, wallet=wallet, username=request.username)


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
