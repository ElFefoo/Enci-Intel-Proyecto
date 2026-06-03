"""
Endpoints de administracion de usuarios — solo rol Admin.
Permite asignar roles Firebase a usuarios del sistema.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.middleware.auth import CurrentUser, require_admin
from app.services.firebase_service import set_user_role, get_user_info, list_users

router = APIRouter()

ROLES_VALIDOS = ["Admin", "Comercial", "Gerencia"]


class SetRoleRequest(BaseModel):
    role: str


@router.get("/admin/users")
async def get_users(user: CurrentUser = Depends(require_admin)):
    """Lista todos los usuarios con sus roles."""
    data = await list_users()
    return {"success": True, "data": data}


@router.get("/admin/users/{uid}")
async def get_user(uid: str, user: CurrentUser = Depends(require_admin)):
    data = await get_user_info(uid)
    return {"success": True, "data": data}


@router.put("/admin/users/{uid}/role")
async def assign_role(uid: str, body: SetRoleRequest, user: CurrentUser = Depends(require_admin)):
    """Asigna custom claim 'role' a un usuario Firebase."""
    if body.role not in ROLES_VALIDOS:
        return {
            "success": False,
            "error": {"code": "INVALID_ROLE", "message": f"Rol invalido. Validos: {ROLES_VALIDOS}"}
        }
    data = await set_user_role(uid, body.role)
    return {"success": True, "data": data}
