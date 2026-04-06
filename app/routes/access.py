"""Routes dla kontroli dostępu."""

from fastapi import APIRouter, Depends, HTTPException, status
from eth_utils import is_address
from sqlalchemy.orm import Session

from app.crud.access_crud import AccessCRUD
from app.crud.audit_crud import AuditCRUD
from app.crud.files_crud import FilesCRUD
from app.crud.folders_crud import FoldersCRUD
from app.crud.user_crud import UserCRUD
from app.database import get_db
from app.dependencies import get_current_wallet
from app.models import AuditAction, User
from app.schemas.access_schemas import (
    AccessInfoResponse,
    GrantAccessRequest,
    RevokeAccessRequest,
    ShareListItem,
)

router = APIRouter(
    prefix="/access",
    tags=["access"]
)


def resolve_wallet_or_username(db: Session, wallet_or_username: str) -> str:
    if is_address(wallet_or_username):
        return wallet_or_username

    user = UserCRUD.get_by_username(db, wallet_or_username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user.wallet


@router.post("/grant")
async def grant_access(
    request: GrantAccessRequest,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    resource_owner = None
    file_id = request.file_id
    folder_id = request.folder_id

    if file_id:
        file = FilesCRUD.get_file_by_id(db, file_id)
        if file:
            resource_owner = file.owner

    if not resource_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    if resource_owner != current_wallet:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can grant access"
        )

    target_wallet = resolve_wallet_or_username(db, request.wallet)

    if target_wallet == current_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot grant access to yourself"
        )

    permission = AccessCRUD.grant_access(
        db=db,
        file_id=file_id,
        user_wallet=target_wallet,
        expiration=request.expiration
    )

    # Zapisz zaszyfrowany CEK dla odbiorcy
    if file_id and request.encrypted_cek:
        FilesCRUD.add_file_key(db, file_id=file_id, wallet=target_wallet, encrypted_key=request.encrypted_cek)

    AuditCRUD.log_action(
        db=db,
        file_id=file_id,
        user_wallet=current_wallet,
        action=AuditAction.PERMISSION_GRANT,
        details=f"Access granted to {target_wallet}"
    )

    return {
        "message": "Access granted successfully",
        "wallet": permission.user_wallet,
        "expiration": permission.expiration
    }


@router.post("/revoke")
async def revoke_access(
    request: RevokeAccessRequest,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    resource_owner = None
    file_id = request.file_id
    folder_id = request.folder_id

    if file_id:
        file = FilesCRUD.get_file_by_id(db, file_id)
        if file:
            resource_owner = file.owner

    if not resource_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    if resource_owner != current_wallet:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can revoke access"
        )

    target_wallet = resolve_wallet_or_username(db, request.wallet)

    revoked = AccessCRUD.revoke_access(
        db=db,
        file_id=file_id,
        user_wallet=target_wallet
    )

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access permission not found"
        )

    AuditCRUD.log_action(
        db=db,
        file_id=file_id,
        user_wallet=current_wallet,
        action=AuditAction.PERMISSION_REVOKE,
        details=f"Access revoked from {target_wallet}"
    )

    return {"message": "Access revoked successfully"}


@router.get("/file/{file_id}", response_model=list[AccessInfoResponse])
async def get_file_permissions(
    file_id: int,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    try:
        file = FilesCRUD.get_file_by_id(db, file_id)

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        if file.owner != current_wallet:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can view permissions"
            )

        permissions = AccessCRUD.get_active_permissions(db, file_id)

        result = []
        for perm in permissions:
            target_user = UserCRUD.get_by_wallet(db, perm.user_wallet)
            result.append(AccessInfoResponse(
                wallet=perm.user_wallet,
                username=target_user.username if target_user else None,
                expiration=perm.expiration,
                granted_at=perm.granted_at
            ))
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR] {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.get("/my-shares", response_model=list[ShareListItem])
async def get_my_shares(
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """Pobierz listę plików, które udostępniłem innym"""
    results = AccessCRUD.get_user_shares(db, current_wallet)
    
    shares = []
    for permission, resource in results:
        # Resolve username for the recipient
        user = UserCRUD.get_by_wallet(db, permission.user_wallet)
        
        is_folder = permission.folder_id is not None
        
        shares.append(ShareListItem(
            file_id=resource.id if not is_folder else None,
            folder_id=resource.id if is_folder else None,
            is_folder=is_folder,
            filename=resource.name if is_folder else (resource.filename or "Unknown"),
            recipient_wallet=permission.user_wallet,
            recipient_username=user.username if user else None,
            expiration=permission.expiration,
            granted_at=permission.granted_at
        ))
        
    return shares
