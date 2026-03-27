"""Schematy Pydantic dla operacji na folderach"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: int | None = None

class FolderUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class FolderMove(BaseModel):
    parent_id: int | None = None

class FolderBreadcrumb(BaseModel):
    id: int
    name: str

class FolderResponse(BaseModel):
    id: int
    name: str
    owner: str
    parent_id: int | None = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MoveItemRequest(BaseModel):
    target_folder_id: int | None = None
    file_ids: list[int] = []
    folder_ids: list[int] = []

from app.schemas.file_schemas import FileListItem

class FolderContentResponse(BaseModel):
    folders: list[FolderResponse]
    files: list[FileListItem]
