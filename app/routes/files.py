"""Routes dla operacji na plikach"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_wallet
from app.crud.files_crud import FilesCRUD
from app.crud.access_crud import AccessCRUD
from app.crud.audit_crud import AuditCRUD
from app.services.file_service import file_service
from app.services.ipfs_service import ipfs_service
from app.schemas.file_schemas import (
    FileUploadResponse,
    FileMetadataResponse,
    FileListItem,
    RenameFileRequest
)
from app.models import AuditAction
from app.config import MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/files",
    tags=["files"]
)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    hash: str = Form(...),
    filename: str = Form(...),
    encryption_type: str = Form(default="AES_256"),
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """
    Wgraj plik

    - **file**: Zaszyfrowany plik (form-data)
    - **hash**: SHA-256 hash pliku (z frontu)
    - **encryption_type**: Typ szyfrowania (default: AES_256)

    WAŻNE: Plik musi być już zaszyfrowany na froncie!
    Backend przechowuje tylko encrypted blob.

    Zwraca file_id i CID
    """
    try:
        # Przeczytaj plik
        file_bytes = await file.read()

        # Sprawdź rozmiar
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            logger.warning(f"File too large: {file_size_mb}MB > {MAX_FILE_SIZE_MB}MB")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size: {MAX_FILE_SIZE_MB}MB"
            )

        # Weryfikuj hash - sprawdź czy plik nie został uszkodzony w transmisji
        calculated_hash = file_service.calculate_hash(file_bytes)
        if calculated_hash != hash:
            logger.error(f"Hash mismatch for user {current_wallet}: {calculated_hash} != {hash}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hash mismatch - file may be corrupted"
            )

        logger.info(f"Uploading file ({file_size_mb:.2f}MB) for {current_wallet}")

        # Wgraj
        result = file_service.upload_file(
            db=db,
            owner=current_wallet,
            file_bytes=file_bytes,
            filename=filename,
            file_hash=hash,
            encryption_type=encryption_type
        )

        return FileUploadResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/my", response_model=list[FileListItem])
async def get_my_files(
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """
    Pobierz swoje pliki (gdzie jesteś właścicielem)
    """
    files = FilesCRUD.get_user_files(db, current_wallet)
    logger.info(f"User {current_wallet} retrieved {len(files)} files")
    return files


@router.get("/shared", response_model=list[FileListItem])
async def get_shared_files(
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """
    Pobierz pliki, które zostały Ci udostępnione
    """
    files = FilesCRUD.get_shared_files(db, current_wallet)
    logger.info(f"User {current_wallet} retrieved {len(files)} shared files")
    return files


@router.get("/{file_id}", response_model=FileMetadataResponse)
async def get_file_metadata(
    file_id: int,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """
    Pobierz metadane pliku

    Wymaga dostępu (właściciel lub przyznany dostęp)
    """
    file = FilesCRUD.get_file_by_id(db, file_id)

    if not file:
        logger.warning(f"File {file_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Sprawdź dostęp
    is_owner = file.owner == current_wallet
    has_access = AccessCRUD.check_user_access(db, file_id, current_wallet)

    if not is_owner and not has_access:
        logger.warning(f"User {current_wallet} tried to access file {file_id} without permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return file


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """
    Pobierz CID pliku (frontend pobierze z IPFS)

    Zwraca CID i loguje akcję
    """
    file = FilesCRUD.get_file_by_id(db, file_id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Sprawdź dostęp
    is_owner = file.owner == current_wallet
    has_access = AccessCRUD.check_user_access(db, file_id, current_wallet)

    if not is_owner and not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Zaloguj akcję
    AuditCRUD.log_action(
        db=db,
        file_id=file_id,
        user_wallet=current_wallet,
        action=AuditAction.DOWNLOAD
    )

    logger.info(f"User {current_wallet} downloaded file {file_id}")
    return {
        "cid": file.cid,
        "message": "Download from IPFS using this CID"
    }


@router.get("/{file_id}/download/raw")
async def download_file_raw(
    file_id: int,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """
    Pobierz zaszyfrowany plik bezpośrednio z backendu

    UWAGA: Plik jest zaszyfrowany!
    Frontend musi go odszyfować.

    Zwraca raw encrypted file bytes.
    """
    file = FilesCRUD.get_file_by_id(db, file_id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Sprawdź dostęp
    is_owner = file.owner == current_wallet
    has_access = AccessCRUD.check_user_access(db, file_id, current_wallet)

    if not is_owner and not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    try:
        # Pobierz z IPFS
        logger.info(f"Fetching file {file_id} from IPFS ({file.cid})")
        file_bytes = ipfs_service.get_file(file.cid)

        # Zaloguj akcję
        AuditCRUD.log_action(
            db=db,
            file_id=file_id,
            user_wallet=current_wallet,
            action=AuditAction.DOWNLOAD
        )

        logger.info(f"User {current_wallet} downloaded raw file {file_id}")

        return Response(
            content=file_bytes,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=file_{file_id}"}
        )
    except Exception as e:
        logger.error(f"Failed to download file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve file from IPFS: {str(e)}"
        )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """
    Usuń plik (tylko właściciel)
    """
    file = FilesCRUD.get_file_by_id(db, file_id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    if file.owner != current_wallet:
        logger.warning(f"User {current_wallet} tried to delete file {file_id} owned by {file.owner}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can delete file"
        )

    if file_service.delete_file(db, file_id, current_wallet):
        logger.info(f"File {file_id} deleted by {current_wallet}")
        return {"message": "File deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete file"
        )


@router.patch("/{file_id}/rename", response_model=FileMetadataResponse)
async def rename_file(
    file_id: int,
    request: RenameFileRequest,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """
    Zmien nazwe pliku (tylko wlasciciel)
    """
    file = FilesCRUD.get_file_by_id(db, file_id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    if file.owner != current_wallet:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can rename file"
        )

    renamed = FilesCRUD.rename_file(db, file_id, request.filename.strip())
    if not renamed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to rename file"
        )

    return renamed

