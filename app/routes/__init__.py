"""Routes package"""

from fastapi import APIRouter

# Importuj wszystkie routery
from app.routes.auth import router as auth_router
from app.routes.files import router as files_router
from app.routes.access import router as access_router
from app.routes.audit import router as audit_router
from app.routes.user import router as user_router
from app.routes.folders import router as folders_router

# Kombinuj wszystkie routery
def get_routers() -> list[APIRouter]:
    """Zwróć listę wszystkich routerów"""
    return [
        auth_router,
        files_router,
        folders_router,
        access_router,
        audit_router,
        user_router,
    ]
