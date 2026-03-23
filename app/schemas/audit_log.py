"""Schematy dla logów audytu"""

from pydantic import BaseModel, field_validator
from datetime import datetime


def validate_wallet(wallet: str) -> str:
    """Walidacja wallet address"""
    if not wallet.startswith("0x") or len(wallet) != 42:
        raise ValueError("Invalid wallet address format")
    return wallet


class AuditLogCreate(BaseModel):
    """Request do logowania akcji"""
    file_id: int
    user_wallet: str
    action: str

    @field_validator("user_wallet")
    @classmethod
    def validate_wallet_field(cls, v):
        return validate_wallet(v)


class AuditLogResponse(BaseModel):
    """Response z danymi loga"""
    id: int
    file_id: int
    user_wallet: str
    action: str
    timestamp: datetime

    class Config:
        from_attributes = True

