"""
Servicio Firebase Admin — operaciones de gestion de usuarios.
Uso principal: asignar custom claims (roles) a usuarios desde el panel Admin.
"""
from firebase_admin import auth as firebase_auth
from app.middleware.auth import _init_firebase


async def set_user_role(uid: str, role: str) -> dict:
    """
    Asigna el rol (custom claim) a un usuario de Firebase.
    Solo puede ser llamado por un Admin desde el endpoint /api/v1/admin/users/{uid}/role

    Roles validos: Admin | Comercial | Gerencia
    """
    _init_firebase()
    firebase_auth.set_custom_user_claims(uid, {"role": role})
    user = firebase_auth.get_user(uid)
    return {
        "uid": user.uid,
        "email": user.email,
        "role": role,
        "displayName": user.display_name,
    }


async def get_user_info(uid: str) -> dict:
    """Obtiene informacion de un usuario Firebase por UID."""
    _init_firebase()
    user = firebase_auth.get_user(uid)
    claims = user.custom_claims or {}
    return {
        "uid": user.uid,
        "email": user.email,
        "displayName": user.display_name,
        "role": claims.get("role"),
        "disabled": user.disabled,
        "createdAt": user.user_metadata.creation_timestamp,
    }


async def list_users(max_results: int = 100) -> list[dict]:
    """Lista todos los usuarios de Firebase con sus roles."""
    _init_firebase()
    users = []
    page = firebase_auth.list_users(max_results=max_results)
    for user in page.users:
        claims = user.custom_claims or {}
        users.append({
            "uid": user.uid,
            "email": user.email,
            "displayName": user.display_name,
            "role": claims.get("role"),
            "disabled": user.disabled,
        })
    return users
