"""Dependency injection dla autentykacji"""

from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from app.services.auth_service import auth_service

# Usunęliśmy nieistniejący import HTTPAuthCredentials


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Dependency do weryfikacji JWT token'u i poboru danych użytkownika

    Użycie:
    @app.get("/protected")
    async def protected_route(user: dict = Depends(get_current_user)):
        return {"wallet": user["wallet"]}
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Wyciągnij token z "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    try:
        payload = auth_service.verify_jwt_token(token)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_wallet(user: dict = Depends(get_current_user)) -> str:
    """
    Dependency do poboru wallet address'u z JWT token'u

    Użycie:
    @app.get("/my-files")
    async def my_files(wallet: str = Depends(get_current_wallet)):
        # wallet zawiera adres użytkownika
        return {"owner": wallet}
    """
    return user.get("wallet")

