"""
Middleware de autenticacion — Firebase Auth (Identity Platform)

MODO DESARROLLO: agregar DISABLE_AUTH=true en backend/.env para
bypasear Firebase completamente. Retorna un usuario Admin mock.
Nunca usar en produccion.
"""
from functools import lru_cache
from typing import Annotated

import firebase_admin
from firebase_admin import auth as firebase_auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)

ROLES_VALIDOS = {"Admin", "Comercial", "Gerencia"}

MOCK_USER_ADMIN = None  # se instancia lazy abajo


@lru_cache
def _init_firebase():
    settings = get_settings()
    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            options={"projectId": settings.firebase_project_id}
        )
    return firebase_admin.get_app()


class CurrentUser:
    def __init__(self, user_id: str, email: str, role: str, name: str = ""):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.name = name

    def is_admin(self) -> bool:
        return self.role == "Admin"

    def is_gerencia(self) -> bool:
        return self.role in ("Admin", "Gerencia")


def _mock_user() -> CurrentUser:
    return CurrentUser(
        user_id="dev-mock-uid-001",
        email="admin@encipharm.cl",
        role="Admin",
        name="Dev Admin",
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> CurrentUser:
    settings = get_settings()

    # ------------------------------------------------------------------ #
    # MODO DESARROLLO — bypass total de Firebase                          #
    # Activar con DISABLE_AUTH=true en backend/.env                       #
    # ------------------------------------------------------------------ #
    if getattr(settings, "disable_auth", False):
        return _mock_user()

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "UNAUTHORIZED", "message": "Token requerido."}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    _init_firebase()

    try:
        decoded = firebase_auth.verify_id_token(credentials.credentials)
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "TOKEN_EXPIRED", "message": "Token expirado."}},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "UNAUTHORIZED", "message": "Token Firebase invalido."}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    role: str | None = decoded.get("role")
    if not role or role not in ROLES_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "NO_ROLE", "message": "Usuario sin rol valido."}},
        )

    return CurrentUser(
        user_id=decoded["uid"],
        email=decoded.get("email", ""),
        role=role,
        name=decoded.get("name", ""),
    )


def require_admin(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "FORBIDDEN", "message": "Requiere rol Admin."}},
        )
    return user


def require_gerencia(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if not user.is_gerencia():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "FORBIDDEN", "message": "Requiere rol Gerencia o Admin."}},
        )
    return user
