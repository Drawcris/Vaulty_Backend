"""CRUD operacje dla audit log'ów"""

from sqlalchemy.orm import Session
from datetime import datetime
from app.models import AuditLog, AuditAction


class AuditCRUD:
    """CRUD operacje dla modelu AuditLog"""

    @staticmethod
    def log_action(
        db: Session,
        file_id: int,
        user_wallet: str,
        action: AuditAction,
        details: str = None
    ) -> AuditLog:
        """Zaloguj akcję w audit log"""
        audit_log = AuditLog(
            file_id=file_id,
            user_wallet=user_wallet,
            action=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    @staticmethod
    def get_file_logs(db: Session, file_id: int) -> list:
        """Pobierz historię akcji dla pliku"""
        return db.query(AuditLog).filter(
            AuditLog.file_id == file_id
        ).order_by(AuditLog.timestamp.desc()).all()

    @staticmethod
    def get_user_logs(db: Session, user_wallet: str) -> list:
        """Pobierz historię akcji użytkownika"""
        return db.query(AuditLog).filter(
            AuditLog.user_wallet == user_wallet
        ).order_by(AuditLog.timestamp.desc()).all()

    @staticmethod
    def get_action_logs(
        db: Session,
        file_id: int,
        action: AuditAction
    ) -> list:
        """Pobierz logi określonej akcji dla pliku"""
        return db.query(AuditLog).filter(
            AuditLog.file_id == file_id,
            AuditLog.action == action
        ).order_by(AuditLog.timestamp.desc()).all()

