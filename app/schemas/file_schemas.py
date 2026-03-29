"""Schematy Pydantic dla operacji na plikach"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FileUploadResponse(BaseModel):
    """Odpowiedz po wgraniu pliku"""

    file_id: int
    cid: str = Field(..., description="IPFS Content Identifier")
    filename: str | None = None
    folder_id: int | None = None
    message: str = "File uploaded successfully"

    model_config = ConfigDict(from_attributes=True)


class FileMetadataResponse(BaseModel):
    """Metadane pliku"""

    id: int
    owner: str = Field(..., description="Wallet adres wlasciciela")
    filename: str | None = None
    cid: str = Field(..., description="IPFS CID")
    hash: str = Field(..., description="Hash pliku")
    encryption_type: str
    upload_date: datetime
    folder_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class FileListItem(BaseModel):
    """Element listy plikow"""

    id: int
    filename: str | None = None
    cid: str
    owner: str | None = None
    owner_username: str | None = None
    encryption_type: str
    upload_date: datetime
    expiration: datetime | None = None
    folder_id: int | None = None
    is_folder: bool = False

    model_config = ConfigDict(from_attributes=True)


class RenameFileRequest(BaseModel):
    """Request do zmiany nazwy pliku"""

    filename: str = Field(..., min_length=1, max_length=255)
