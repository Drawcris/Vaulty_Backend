"""Schematy Pydantic dla audit log'ów"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models import AuditAction


class AuditLogResponse(BaseModel):
    """Wpis w audit log'u"""
    id: int
    file_id: int
    user_wallet: str
    action: AuditAction
    timestamp: datetime
    details: str = None

    model_config = ConfigDict(from_attributes=True)

