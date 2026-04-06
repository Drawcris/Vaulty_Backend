"""CRUD operacje dla plikow"""

from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import AccessPermission, File, User, FileKey

class FilesCRUD:
    """CRUD operacje dla modelu File"""

    @staticmethod
    def add_file_key(db: Session, file_id: int, wallet: str, encrypted_key: str) -> FileKey:
        file_key = FileKey(file_id=file_id, wallet=wallet, encrypted_key=encrypted_key)
        db.add(file_key)
        db.commit()
        db.refresh(file_key)
        return file_key

    @staticmethod
    def get_file_key(db: Session, file_id: int, wallet: str) -> FileKey | None:
        return db.query(FileKey).filter(FileKey.file_id == file_id, FileKey.wallet.ilike(wallet)).first()

    @staticmethod
    def create_file(
        db: Session,
        owner: str,
        filename: str,
        cid: str,
        hash: str,
        encryption_type: str = "AES_256",
        folder_id: int | None = None
    ) -> File:
        file = File(
            owner=owner,
            filename=filename,
            cid=cid,
            hash=hash,
            encryption_type=encryption_type,
            folder_id=folder_id
        )
        db.add(file)
        db.commit()
        db.refresh(file)
        return file

    @staticmethod
    def get_file_by_id(db: Session, file_id: int) -> File | None:
        return db.query(File).filter(File.id == file_id).first()

    @staticmethod
    def get_file_by_hash(db: Session, file_hash: str) -> File | None:
        return db.query(File).filter(File.hash == file_hash).first()

    @staticmethod
    def get_user_files(db: Session, owner: str, folder_id: int | None = None) -> list[File]:
        return db.query(File).filter(
            File.owner == owner,
            File.folder_id == folder_id
        ).order_by(File.upload_date.desc()).all()

    @staticmethod
    def get_shared_files(db: Session, wallet: str):
        # Join with AccessPermission to get expiration and User to get owner_username
        results = db.query(File, User.username, AccessPermission.expiration).join(
            AccessPermission, AccessPermission.file_id == File.id
        ).outerjoin(
            User, User.wallet.ilike(File.owner)
        ).filter(
            and_(
                AccessPermission.user_wallet.ilike(wallet),
                (AccessPermission.expiration.is_(None) | (AccessPermission.expiration > datetime.utcnow()))
            )
        ).order_by(File.upload_date.desc()).all()

        # Map results to objects that match FileListItem schema
        files_with_metadata = []
        for file, username, expiration in results:
            file_dict = {
                "id": file.id,
                "filename": file.filename,
                "cid": file.cid,
                "owner": file.owner,
                "owner_username": username or "Nieznany",
                "encryption_type": file.encryption_type,
                "upload_date": file.upload_date,
                "expiration": expiration,
                "folder_id": file.folder_id,
                "is_folder": False
            }
            files_with_metadata.append(file_dict)
            
        return files_with_metadata

    @staticmethod
    def delete_file(db: Session, file_id: int) -> bool:
        file = db.query(File).filter(File.id == file_id).first()
        if file:
            db.delete(file)
            db.commit()
            return True
        return False

    @staticmethod
    def get_file_by_cid(db: Session, cid: str) -> File | None:
        return db.query(File).filter(File.cid == cid).first()

    @staticmethod
    def rename_file(db: Session, file_id: int, filename: str) -> File | None:
        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            return None

        file.filename = filename
        db.commit()
        db.refresh(file)
        return file
