"""CRUD operacje dla kontroli dostępu"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from app.models import AccessPermission


class AccessCRUD:
    """CRUD operacje dla modelu AccessPermission"""

    @staticmethod
    def grant_access(
        db: Session,
        file_id: int,
        user_wallet: str,
        expiration: datetime = None
    ) -> AccessPermission:
        """Przyznaj dostęp do pliku"""
        # Sprawdź czy dostęp już istnieje
        existing = db.query(AccessPermission).filter(
            and_(
                AccessPermission.file_id == file_id,
                AccessPermission.user_wallet == user_wallet
            )
        ).first()

        if existing:
            # Aktualizuj istniejący dostęp
            existing.expiration = expiration
            db.commit()
            db.refresh(existing)
            return existing

        # Stwórz nowy dostęp
        permission = AccessPermission(
            file_id=file_id,
            user_wallet=user_wallet,
            expiration=expiration
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission

    @staticmethod
    def revoke_access(db: Session, file_id: int, user_wallet: str) -> bool:
        """Cofnij dostęp do pliku"""
        permission = db.query(AccessPermission).filter(
            and_(
                AccessPermission.file_id == file_id,
                AccessPermission.user_wallet == user_wallet
            )
        ).first()

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
        """Sprawdź czy użytkownik ma dostęp do pliku"""
        permission = db.query(AccessPermission).filter(
            and_(
                AccessPermission.file_id == file_id,
                AccessPermission.user_wallet == user_wallet
            )
        ).first()

        if not permission:
            return False

        # Sprawdź czy dostęp nie wygasł
        if permission.expiration:
            if permission.expiration < datetime.utcnow():
                return False

        return True

    @staticmethod
    def get_active_permissions(db: Session, file_id: int) -> list:
        """Pobierz aktywne uprawnienia (niewygas­łe)"""
        permissions = db.query(AccessPermission).filter(
            AccessPermission.file_id == file_id
        ).all()

        # Filtruj wygas­łe
        active = [
            p for p in permissions
            if p.expiration is None or p.expiration > datetime.utcnow()
        ]
        return active

