"""Routes dla operacji na folderach"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_wallet
from app.crud.folders_crud import FoldersCRUD
from app.crud.files_crud import FilesCRUD
from app.models import File, Folder
from app.schemas.folder_schemas import (
    FolderCreate,
    FolderUpdate,
    FolderResponse,
    MoveItemRequest,
    FolderBreadcrumb,
    FolderContentResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/folders",
    tags=["folders"]
)

@router.post("", response_model=FolderResponse)
async def create_folder(
    request: FolderCreate,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """Tworzy nowy folder"""
    if request.parent_id:
        parent = FoldersCRUD.get_folder_by_id(db, request.parent_id)
        if not parent or parent.owner != current_wallet:
            raise HTTPException(status_code=404, detail="Parent folder not found")
            
    try:
        folder = FoldersCRUD.create_folder(
            db=db,
            name=request.name.strip(),
            owner=current_wallet,
            parent_id=request.parent_id
        )
        return folder
    except Exception as e:
        logger.error(f"Failed to create folder: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to create folder")


@router.get("/all", response_model=list[FolderResponse])
async def get_all_folders(
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """Pobiera wszystkie foldery uzytkownika plasko (do drzew/selectow)"""
    return db.query(Folder).filter(Folder.owner == current_wallet).order_by(Folder.name).all()

@router.get("/root/contents", response_model=FolderContentResponse)
async def get_root_contents(
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """Pobiera zawartość korzenia dysku"""
    folders = FoldersCRUD.get_user_folders(db, current_wallet, None)
    files = FilesCRUD.get_user_files(db, current_wallet, None)
    return {"folders": folders, "files": files}

@router.post("/move")
async def move_items(
    request: MoveItemRequest,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """Przenosi foldery i/lub pliki do wybranego folderu (lub roota)"""
    new_parent_id = request.target_folder_id
    
    if new_parent_id:
        target = FoldersCRUD.get_folder_by_id(db, new_parent_id)
        if not target or target.owner != current_wallet:
            raise HTTPException(status_code=404, detail="Target folder not found")
            
    for f_id in request.folder_ids:
        # TODO zoptymalizowac.
        FoldersCRUD.move_folder(db, f_id, new_parent_id)
        
    for file_id in request.file_ids:
        # TODO wyniesc do FilesCRUD.move_file
        file = FilesCRUD.get_file_by_id(db, file_id)
        if file and file.owner == current_wallet:
            file.folder_id = new_parent_id
            db.commit()
            
    return {"message": "Items moved successfully"}

@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: int,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    folder = FoldersCRUD.get_folder_by_id(db, folder_id)
    if not folder or folder.owner != current_wallet:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.patch("/{folder_id}/rename", response_model=FolderResponse)
async def rename_folder(
    folder_id: int,
    request: FolderUpdate,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    folder = FoldersCRUD.get_folder_by_id(db, folder_id)
    if not folder or folder.owner != current_wallet:
        raise HTTPException(status_code=404, detail="Folder not found")
        
    if FoldersCRUD.rename_folder(db, folder_id, request.name.strip()):
        return FoldersCRUD.get_folder_by_id(db, folder_id)
    raise HTTPException(status_code=400, detail="Failed to rename folder")


@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: int,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    # Uwaga: Opcja kaskadowa powinna zadbać o dzieci lub ustawiana na null (zależnie od modelu)
    # W modelu zdefiniowaliśmy cascade="all, delete-orphan", więc podkatalogi i uprawnienia znikną.
    # Pliki dla uproszczenia ustawiają folder_id na SET NULL lub można napisać logikę kasującą.
    # Ustaliliśmy ondelete="SET NULL" dla files.folder_id, wiąc wylądują w root. Możemy to zmienić ręcznie tu.
    
    folder = FoldersCRUD.get_folder_by_id(db, folder_id)
    if not folder or folder.owner != current_wallet:
        raise HTTPException(status_code=404, detail="Folder not found")
        
    if FoldersCRUD.delete_folder(db, folder_id):
        return {"message": "Folder deleted"}
    raise HTTPException(status_code=400, detail="Failed to delete folder")


@router.get("/{folder_id}/breadcrumbs", response_model=list[FolderBreadcrumb])
async def get_breadcrumbs(
    folder_id: int,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    folder = FoldersCRUD.get_folder_by_id(db, folder_id)
    if not folder or folder.owner != current_wallet:
        raise HTTPException(status_code=404, detail="Folder not found")
        
    return FoldersCRUD.get_breadcrumbs(db, folder_id)




@router.get("/{folder_id}/contents", response_model=FolderContentResponse)
async def get_folder_contents(
    folder_id: int,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    folder = FoldersCRUD.get_folder_by_id(db, folder_id)
    if not folder or folder.owner != current_wallet:
        raise HTTPException(status_code=404, detail="Folder not found")
        
    folders = FoldersCRUD.get_user_folders(db, current_wallet, folder_id)
    files = FilesCRUD.get_user_files(db, current_wallet, folder_id)
    return {"folders": folders, "files": files}


