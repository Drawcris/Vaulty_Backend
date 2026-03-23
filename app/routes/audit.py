"""Routes dla audit log'ów"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_wallet
from app.crud.files_crud import FilesCRUD
from app.crud.audit_crud import AuditCRUD
from app.schemas.audit_schemas import AuditLogResponse

router = APIRouter(
    prefix="/audit",
    tags=["audit"]
)


@router.get("/file/{file_id}")
async def get_file_audit_logs(
    file_id: int,
    current_wallet: str = Depends(get_current_wallet),
    db: Session = Depends(get_db)
):
    """
    Pobierz historię akcji dla pliku

    Tylko właściciel może zobaczyć pełne logi
    """
    try:
        # Pobierz plik
        file = FilesCRUD.get_file_by_id(db, file_id)

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        # Sprawdź czy jesteś właścicielem
        if file.owner != current_wallet:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can view audit logs"
            )

        # Pobierz logi
        logs = AuditCRUD.get_file_logs(db, file_id)
        
        # Konwertuj do dicts aby łatwo serializować
        return [
            {
                "id": log.id,
                "file_id": log.file_id,
                "user_wallet": log.user_wallet,
                "action": log.action.value,  # Konwertuj enum na string
                "timestamp": log.timestamp,
                "details": log.details
            }
            for log in logs
        ]
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

