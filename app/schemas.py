"""Pydantic schematy dla requestów i responsów"""

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


class TokenPayload(BaseModel):
    """Payload JWT token'u"""
    wallet: str
    exp: Optional[datetime] = None


# File schemy
class FileCreate(BaseModel):
    """Request do stworzenia pliku"""
    cid: str
    hash: str
    encryption_type: str = "AES_256"


class FileResponse(BaseModel):
    """Response z danymi pliku"""
    id: int
    owner: str
    cid: str
    hash: str
    encryption_type: str
    upload_date: datetime

    class Config:
        from_attributes = True


# AccessPermission schemy
class AccessPermissionCreate(BaseModel):
    """Request do nadania dostępu"""
    file_id: Optional[int] = None
    folder_id: Optional[int] = None
    user_wallet: str
    expiration: Optional[datetime] = None

    @field_validator("user_wallet")
    @classmethod
    def validate_wallet_field(cls, v):
        return validate_wallet(v)


class AccessPermissionResponse(BaseModel):
    """Response z danymi dostępu"""
    id: int
    file_id: Optional[int]
    folder_id: Optional[int]
    user_wallet: str
    expiration: Optional[datetime]
    granted_at: datetime

    class Config:
        from_attributes = True


# AuditLog schemy
class AuditLogCreate(BaseModel):
    """Request do logowania akcji"""
    file_id: Optional[int] = None
    folder_id: Optional[int] = None
    user_wallet: str
    action: str

    @field_validator("user_wallet")
    @classmethod
    def validate_wallet_field(cls, v):
        return validate_wallet(v)


class AuditLogResponse(BaseModel):
    """Response z danymi loga"""
    id: int
    file_id: Optional[int]
    folder_id: Optional[int]
    user_wallet: str
    action: str
    timestamp: datetime

    class Config:
        from_attributes = True


