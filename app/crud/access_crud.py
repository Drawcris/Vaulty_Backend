"""CRUD operacje dla kontroli dostępu"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from app.models import AccessPermission, File


class AccessCRUD:
    """CRUD operacje dla modelu AccessPermission"""

    @staticmethod
    def grant_access(
        db: Session,
        user_wallet: str,
        file_id: int = None,
        folder_id: int = None,
        expiration: datetime = None
    ) -> AccessPermission:
        """Przyznaj dostęp do pliku LUB folderu"""
        # Sprawdź czy dostęp już istnieje
        query = db.query(AccessPermission).filter(
            AccessPermission.user_wallet.ilike(user_wallet)
        )
        if file_id:
            query = query.filter(AccessPermission.file_id == file_id)
        elif folder_id:
            query = query.filter(AccessPermission.folder_id == folder_id)
        
        existing = query.first()

        if existing:
            # Aktualizuj istniejący dostęp
            existing.expiration = expiration
            db.commit()
            db.refresh(existing)
            return existing

        # Stwórz nowy dostęp
        permission = AccessPermission(
            file_id=file_id,
            folder_id=folder_id,
            user_wallet=user_wallet,
            expiration=expiration
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission

    @staticmethod
    def revoke_access(db: Session, user_wallet: str, file_id: int = None, folder_id: int = None) -> bool:
        """Cofnij dostęp do pliku lub folderu"""
        query = db.query(AccessPermission).filter(
            AccessPermission.user_wallet.ilike(user_wallet)
        )
        if file_id:
            query = query.filter(AccessPermission.file_id == file_id)
        elif folder_id:
            query = query.filter(AccessPermission.folder_id == folder_id)
            
        permission = query.first()

        if permission:
            db.delete(permission)
            db.commit()
            return True
        return False

    @staticmethod
    def get_file_permissions(db: Session, file_id: int) -> list:
        """Pobierz listę użytkowników z dostępem do pliku"""
        return db.query(AccessPermission).filter(
            AccessPermission.file_id == file_id
        ).all()

    @staticmethod
    def check_user_access(
        db: Session,
        file_id: int,
        user_wallet: str
    ) -> bool:
        """
        Sprawdź czy użytkownik ma bezpośredni dostęp do pliku.
        """
        permission = db.query(AccessPermission).filter(
            and_(
                AccessPermission.file_id == file_id,
                AccessPermission.user_wallet.ilike(user_wallet)
            )
        ).first()

        if permission and (not permission.expiration or permission.expiration > datetime.utcnow()):
            return True

        return False

    @staticmethod
    def get_active_permissions(db: Session, file_id: int) -> list:
        permissions = db.query(AccessPermission).filter(
            AccessPermission.file_id == file_id
        ).all()
        return [p for p in permissions if p.expiration is None or p.expiration > datetime.utcnow()]

    @staticmethod
    def get_user_shares(db: Session, owner_wallet: str):
        from app.models import Folder
        # Udostępnione pliki
        file_shares = db.query(AccessPermission, File).join(
            File, AccessPermission.file_id == File.id
        ).filter(
            File.owner.ilike(owner_wallet)
        ).all()
        
        # Udostępnione foldery
        folder_shares = db.query(AccessPermission, Folder).join(
            Folder, AccessPermission.folder_id == Folder.id
        ).filter(
            Folder.owner.ilike(owner_wallet)
        ).all()
        
        return file_shares + folder_shares
