"""
Dependencia de autenticación para FastAPI.

Modos:
  DISABLE_AUTH=true  → bypass completo (desarrollo local)
  DISABLE_AUTH=false → valida Firebase ID Token con firebase-admin
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    # --- Modo desarrollo: bypass total ---
    if settings.disable_auth:
        return {
            "uid": "dev-user-001",
            "email": "admin@encipharm.cl",
            "role": "Admin",
        }

    # --- Produccion: validar Firebase ID Token ---
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Token JWT ausente."},
        )

    try:
        import firebase_admin
        from firebase_admin import auth as firebase_auth

        # Inicializar Firebase Admin si no está inicializado
        if not firebase_admin._apps:
            firebase_admin.initialize_app()

        decoded = firebase_auth.verify_id_token(credentials.credentials)

        return {
            "uid": decoded["uid"],
            "email": decoded.get("email", ""),
            "role": decoded.get("role", "Comercial"),  # custom claim
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": f"Token inválido o expirado: {str(e)}"},
        )


def require_role(*roles: str):
    """Dependencia de rol. Ejemplo: Depends(require_role('Admin', 'Gerencia'))"""
    async def _check(user: dict = Depends(get_current_user)) -> dict:
        if settings.disable_auth:
            return user
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": f"Rol requerido: {', '.join(roles)}"},
            )
        return user
    return _check
