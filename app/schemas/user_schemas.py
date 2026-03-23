"""Schematy Pydantic dla użytkowników i username."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


UsernameValue = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_]+$"
    )
]


class UserResponse(BaseModel):
    wallet: str
    username: str | None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SetUsernameRequest(BaseModel):
    username: UsernameValue


class WalletLookupResponse(BaseModel):
    wallet: str
