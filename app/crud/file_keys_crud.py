"""
FileKey CRUD – zarządzanie zaszyfrowanymi kluczami plików.

ARCHITEKTURA:
  Każdy plik ma swój losowy klucz (file_key).
  Klucz jest szyfrowany osobno dla każdego użytkownika mającego dostęp.
  Backend przechowuje encrypted_file_key – nigdy plaintext file_key.

TODO (Etap 3 – Hybrid Encryption):
  - Implementacja pełnego flow upload/download z file_key
  - Re-encryption klucza przy sharing
"""

import logging
from sqlalchemy.orm import Session
from app.models import FileKey

logger = logging.getLogger(__name__)


class FileKeysCRUD:
    """CRUD dla zaszyfrowanych kluczy plików."""

    @staticmethod
    def create_key(db: Session, file_id: int, wallet: str, encrypted_key: str) -> FileKey:
        """
        Zapisz zaszyfrowany klucz pliku dla danego użytkownika.

        Args:
            db:            sesja bazy danych
            file_id:       ID pliku
            wallet:        adres portfela użytkownika
            encrypted_key: klucz AES zaszyfrowany kluczem użytkownika (base64)

        Returns:
            Nowo utworzony rekord FileKey
        """
        existing = FileKeysCRUD.get_key(db, file_id, wallet)
        if existing:
            # Aktualizuj jeśli już istnieje (np. re-encryption)
            existing.encrypted_key = encrypted_key
            db.commit()
            db.refresh(existing)
            logger.info(f"[FileKeys] Updated key for file={file_id} wallet={wallet}")
            return existing

        key = FileKey(
            file_id=file_id,
            wallet=wallet,
            encrypted_key=encrypted_key
        )
        db.add(key)
        db.commit()
        db.refresh(key)
        logger.info(f"[FileKeys] Created key for file={file_id} wallet={wallet}")
        return key

    @staticmethod
    def get_key(db: Session, file_id: int, wallet: str) -> FileKey | None:
        """
        Pobierz zaszyfrowany klucz pliku dla danego użytkownika.

        Returns:
            FileKey lub None jeśli nie istnieje
        """
        return db.query(FileKey).filter(
            FileKey.file_id == file_id,
            FileKey.wallet == wallet
        ).first()

    @staticmethod
    def delete_key(db: Session, file_id: int, wallet: str) -> bool:
        """Usuń klucz przy cofaniu dostępu."""
        key = FileKeysCRUD.get_key(db, file_id, wallet)
        if not key:
            return False
        db.delete(key)
        db.commit()
        logger.info(f"[FileKeys] Deleted key for file={file_id} wallet={wallet}")
        return True

    @staticmethod
    def get_all_keys_for_file(db: Session, file_id: int) -> list[FileKey]:
        """Pobierz wszystkie klucze dla danego pliku (właściciel + udostępnieni)."""
        return db.query(FileKey).filter(FileKey.file_id == file_id).all()
