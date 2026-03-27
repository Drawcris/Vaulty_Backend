"""CRUD operacje dla folderów"""

from sqlalchemy.orm import Session
from app.models import Folder, File

class FoldersCRUD:
    @staticmethod
    def create_folder(db: Session, name: str, owner: str, parent_id: int | None = None) -> Folder:
        folder = Folder(name=name, owner=owner, parent_id=parent_id)
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def get_folder_by_id(db: Session, folder_id: int) -> Folder | None:
        return db.query(Folder).filter(Folder.id == folder_id).first()

    @staticmethod
    def get_user_folders(db: Session, owner: str, parent_id: int | None = None) -> list[Folder]:
        return db.query(Folder).filter(
            Folder.owner == owner,
            Folder.parent_id == parent_id
        ).order_by(Folder.name.asc()).all()

    @staticmethod
    def rename_folder(db: Session, folder_id: int, name: str) -> bool:
        folder = db.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            return False
        folder.name = name
        db.commit()
        return True

    @staticmethod
    def delete_folder(db: Session, folder_id: int) -> bool:
        folder = db.query(Folder).filter(Folder.id == folder_id).first()
        if folder:
            db.delete(folder)
            db.commit()
            return True
        return False

    @staticmethod
    def move_folder(db: Session, folder_id: int, new_parent_id: int | None) -> bool:
        folder = db.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            return False
            
        # Zapobieganie pętli (nie przenoś do samego siebie ani swoich dzieci)
        # Dla uproszczenia magisterki pomijamy skomplikowane sprawdzanie pętli głębokiej,
        # ale przynajmniej zablokujmy przenoszenie do samego siebie.
        if folder.id == new_parent_id:
            return False

        folder.parent_id = new_parent_id
        db.commit()
        return True

    @staticmethod
    def get_breadcrumbs(db: Session, folder_id: int) -> list[dict]:
        """Pobiera ścieżkę do roota."""
        breadcrumbs = []
        current_id = folder_id

        while current_id is not None:
            folder = FoldersCRUD.get_folder_by_id(db, current_id)
            if not folder:
                break
            breadcrumbs.insert(0, {"id": folder.id, "name": folder.name})
            current_id = folder.parent_id
            
        return breadcrumbs
