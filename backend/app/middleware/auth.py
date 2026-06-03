"""
Middleware de autenticacion — Firebase Auth (Identity Platform)

Flujo:
  1. Frontend hace login con Firebase Auth SDK (email/password u OAuth)
  2. Firebase emite un ID Token JWT firmado por Google
  3. Frontend envia el token en cada request: Authorization: Bearer <id_token>
  4. Este middleware verifica el token con firebase-admin (sin red — usa clave publica de Google)
  5. Lee el custom claim 'role' (Admin | Comercial | Gerencia) asignado via Admin SDK

En Cloud Run: firebase_admin usa Application Default Credentials automaticamente.
En local: requiere GOOGLE_APPLICATION_CREDENTIALS apuntando a serviceAccountKey.json
"""
from functools import lru_cache
from typing import Annotated

import firebase_admin
from firebase_admin import auth as firebase_auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

bearer_scheme = HTTPBearer()

ROLES_VALIDOS = {"Admin", "Comercial", "Gerencia"}


@lru_cache
def _init_firebase():
    """Inicializa Firebase Admin SDK una sola vez (singleton)."""
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


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> CurrentUser:
    """Dependencia FastAPI — verifica ID Token de Firebase y extrae el usuario."""
    _init_firebase()

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "error": {"code": "UNAUTHORIZED", "message": "Token Firebase invalido o expirado."},
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        decoded = firebase_auth.verify_id_token(credentials.credentials)
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "TOKEN_EXPIRED", "message": "Token expirado. Vuelve a iniciar sesion."}},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise credentials_exception

    role: str | None = decoded.get("role")
    if not role or role not in ROLES_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {"code": "NO_ROLE", "message": f"Usuario sin rol valido. Contacta al administrador."},
            },
        )

    return CurrentUser(
        user_id=decoded["uid"],
        email=decoded.get("email", ""),
        role=role,
        name=decoded.get("name", ""),
    )


def require_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Dependencia que exige rol Admin."""
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "FORBIDDEN", "message": "Requiere rol Admin."}},
        )
    return user


def require_gerencia(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Dependencia que exige rol Admin o Gerencia."""
    if not user.is_gerencia():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "FORBIDDEN", "message": "Requiere rol Gerencia o Admin."}},
        )
    return user
