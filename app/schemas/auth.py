"""Schematy dla autentykacji"""

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


def validate_wallet(wallet: str) -> str:
    """Walidacja wallet address"""
    if not wallet.startswith("0x") or len(wallet) != 42:
        raise ValueError("Invalid wallet address format")
    return wallet


class ChallengeRequest(BaseModel):
    """Request do żądania challenge'u do podpisania"""
    wallet: str

    @field_validator("wallet")
    @classmethod
    def validate_wallet_field(cls, v):
        return validate_wallet(v)


class ChallengeResponse(BaseModel):
    """Response z challenge'em do podpisania"""
    challenge: str
    wallet: str


class VerifySignatureRequest(BaseModel):
    """Request do weryfikacji podpisu"""
    wallet: str
    signature: str

    @field_validator("wallet")
    @classmethod
    def validate_wallet_field(cls, v):
        return validate_wallet(v)


class VerifySignatureResponse(BaseModel):
    """Response z JWT token'em"""
    token: str
    wallet: str
    message: str = "Login successful"
    username_required: bool = False
    username: Optional[str] = None


class TokenPayload(BaseModel):
    """Payload JWT token'u"""
    wallet: str
    exp: Optional[datetime] = None

