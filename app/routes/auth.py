"""Router dla Web3 autentykacji."""

from fastapi import APIRouter, Depends, HTTPException, status
from eth_utils import is_address
from sqlalchemy.orm import Session

from app.crud.user_crud import UserCRUD
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas import (
    ChallengeRequest,
    ChallengeResponse,
    VerifySignatureRequest,
    VerifySignatureResponse,
)
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/challenge", response_model=ChallengeResponse)
async def request_challenge(request: ChallengeRequest):
    if not request.wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet address jest wymagany"
        )

    if not is_address(request.wallet):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Niepoprawny format wallet address"
        )

    try:
        challenge = auth_service.generate_challenge(request.wallet)
        return ChallengeResponse(
            challenge=challenge,
            wallet=request.wallet
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd przy generowaniu challenge'u: {str(e)}"
        )


@router.post("/verify", response_model=VerifySignatureResponse)
async def verify_signature(
    request: VerifySignatureRequest,
    db: Session = Depends(get_db)
):
    if not request.wallet or not request.signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet i signature są wymagane"
        )

    if not is_address(request.wallet):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Niepoprawny format wallet address"
        )

    try:
        if not auth_service.verify_challenge_exists(request.wallet):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge nie istnieje lub wygasł. Żądaj nowego challenge'u."
            )

        if not auth_service.verify_signature(request.wallet, request.signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Niepoprawny podpis"
            )

        auth_service.clear_challenge(request.wallet)
        token = auth_service.create_jwt_token(request.wallet)
        user = UserCRUD.get_by_wallet(db, request.wallet)

        return VerifySignatureResponse(
            token=token,
            wallet=request.wallet,
            username_required=user is None,
            username=user.username if user else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd przy weryfikacji podpisu: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wallet = user.get("wallet")
    user_record = UserCRUD.get_by_wallet(db, wallet)

    return {
        "wallet": wallet,
        "username": user_record.username if user_record else None,
        "authenticated": True,
        "exp": user.get("exp"),
        "username_required": user_record is None
    }
