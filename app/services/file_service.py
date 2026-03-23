"""Service do obslugi operacji na plikach"""

import hashlib

from sqlalchemy.orm import Session

from app.crud.audit_crud import AuditCRUD
from app.crud.files_crud import FilesCRUD
from app.models import AuditAction
from app.services.ipfs_service import ipfs_service


class FileService:
    """Service do obslugi plikow"""

    @staticmethod
    def calculate_hash(file_bytes: bytes) -> str:
      """Oblicz SHA-256 hash pliku"""
      return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def upload_file(
        db: Session,
        owner: str,
        file_bytes: bytes,
        filename: str,
        file_hash: str | None = None,
        encryption_type: str = "AES_256"
    ) -> dict:
        """
        Wgraj plik do IPFS i zapisz metadata w bazie.
        """
        file_hash = file_hash or FileService.calculate_hash(file_bytes)

        existing = FilesCRUD.get_file_by_hash(db, file_hash)
        if existing:
            return {
                "file_id": existing.id,
                "cid": existing.cid,
                "filename": existing.filename,
                "message": "File already exists"
            }

        try:
            cid = ipfs_service.upload_file(file_bytes)
        except Exception as exc:
            raise Exception(f"Failed to upload to IPFS: {str(exc)}")

        file_record = FilesCRUD.create_file(
            db=db,
            owner=owner,
            filename=filename,
            cid=cid,
            hash=file_hash,
            encryption_type=encryption_type
        )

        AuditCRUD.log_action(
            db=db,
            file_id=file_record.id,
            user_wallet=owner,
            action=AuditAction.UPLOAD,
            details=f"File uploaded with CID: {cid}"
        )

        return {
            "file_id": file_record.id,
            "cid": cid,
            "filename": file_record.filename,
            "message": "File uploaded successfully"
        }

    @staticmethod
    def delete_file(db: Session, file_id: int, owner: str) -> bool:
        """
        Usun plik tylko dla wlasciciela.
        """
        file = FilesCRUD.get_file_by_id(db, file_id)

        if not file or file.owner != owner:
            return False

        AuditCRUD.log_action(
            db=db,
            file_id=file_id,
            user_wallet=owner,
            action=AuditAction.DELETE
        )

        return FilesCRUD.delete_file(db, file_id)


file_service = FileService()
