"""Schematy dla plików"""

from pydantic import BaseModel
from datetime import datetime


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

