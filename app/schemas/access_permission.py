"""Schematy dla uprawnień dostępu"""

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


def validate_wallet(wallet: str) -> str:
    """Walidacja wallet address"""
    if not wallet.startswith("0x") or len(wallet) != 42:
        raise ValueError("Invalid wallet address format")
    return wallet


class AccessPermissionCreate(BaseModel):
    """Request do nadania dostępu"""
    file_id: int
    user_wallet: str
    expiration: Optional[datetime] = None

    @field_validator("user_wallet")
    @classmethod
    def validate_wallet_field(cls, v):
        return validate_wallet(v)


class AccessPermissionResponse(BaseModel):
    """Response z danymi dostępu"""
    id: int
    file_id: int
    user_wallet: str
    expiration: Optional[datetime]
    granted_at: datetime

    class Config:
        from_attributes = True

