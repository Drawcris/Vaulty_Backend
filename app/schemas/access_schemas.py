"""Schematy Pydantic dla kontroli dostępu."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GrantAccessRequest(BaseModel):
    """Żądanie przyznania dostępu do pliku LUB folderu."""

    file_id: Optional[int] = None
    folder_id: Optional[int] = None
    wallet: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Ethereum wallet address lub username odbiorcy"
    )
    expiration: Optional[datetime] = Field(
        None,
        description="Data wygaśnięcia dostępu (null = bez limitu)"
    )

    model_config = ConfigDict(from_attributes=True)


class RevokeAccessRequest(BaseModel):
    """Żądanie cofnięcia dostępu."""

    file_id: Optional[int] = None
    folder_id: Optional[int] = None
    wallet: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Ethereum wallet address lub username odbiorcy"
    )

    model_config = ConfigDict(from_attributes=True)


class AccessInfoResponse(BaseModel):
    """Informacje o dostępie do pliku."""

    wallet: str
    username: Optional[str] = None
    expiration: Optional[datetime]
    granted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShareListItem(BaseModel):
    """Informacja o pliku udostępnionym komuś (widok właściciela)"""

    file_id: Optional[int] = None
    folder_id: Optional[int] = None
    is_folder: bool = False
    filename: str
    recipient_wallet: str
    recipient_username: Optional[str] = None
    expiration: Optional[datetime]
    granted_at: datetime

    model_config = ConfigDict(from_attributes=True)
