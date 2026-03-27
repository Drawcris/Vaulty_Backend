from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class AuditAction(str, enum.Enum):
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"
    SHARE = "SHARE"
    DELETE = "DELETE"
    PERMISSION_GRANT = "PERMISSION_GRANT"
    PERMISSION_REVOKE = "PERMISSION_REVOKE"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    wallet = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<User(wallet={self.wallet}, username={self.username})>"


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    parent = relationship("Folder", remote_side=[id], back_populates="subfolders")
    subfolders = relationship("Folder", back_populates="parent", cascade="all, delete-orphan")
    files = relationship("File", back_populates="folder")

    def __repr__(self):
        return f"<Folder(id={self.id}, name={self.name}, owner={self.owner})>"


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=True, index=True)
    cid = Column(String(512), nullable=False, unique=True, index=True)  # IPFS CID
    hash = Column(String(512), nullable=False, unique=True, index=True)
    encryption_type = Column(Text, default="AES_256", nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True)

    folder = relationship("Folder", back_populates="files")
    access_permissions = relationship("AccessPermission", back_populates="file", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="file", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<File(id={self.id}, owner={self.owner}, cid={self.cid})>"

class AccessPermission(Base):
    __tablename__ = "access_permissions"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    user_wallet = Column(String(512), nullable=False, index=True)
    expiration = Column(DateTime, nullable=True)  # NULL = brak wygaśnięcia
    granted_at = Column(DateTime, default=datetime.utcnow)

    file = relationship("File", back_populates="access_permissions")

    def __repr__(self):
        return f"<AccessPermission(file_id={self.file_id}, user_wallet={self.user_wallet})>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    user_wallet = Column(String(512), nullable=False, index=True)
    action = Column(Enum(AuditAction), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    details = Column(Text, nullable=True)  # Dodatkowe informacje o akcji

    # Relacja
    file = relationship("File", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(file_id={self.file_id}, action={self.action}, timestamp={self.timestamp})>"

