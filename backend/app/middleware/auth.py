"""Middleware JWT — Keycloak OIDC"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
import httpx
from app.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer()
_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(settings.keycloak_jwks_url)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


class CurrentUser:
    def __init__(self, user_id: str, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role

    def is_admin(self) -> bool:
        return self.role == "Admin"


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]
) -> CurrentUser:
    token = credentials.credentials
    err = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"success": False, "error": {"code": "UNAUTHORIZED", "message": "Token JWT inválido o expirado."}},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        jwks = await _get_jwks()
        payload = jwt.decode(token, jwks, algorithms=["RS256"], options={"verify_aud": False})
        user_id: str = payload.get("sub")
        email: str = payload.get("email", "")
        roles: list = payload.get("realm_access", {}).get("roles", [])
        role = next((r for r in roles if r in ("Admin", "Comercial", "Gerencia")), None)
        if not user_id or not role:
            raise err
        return CurrentUser(user_id=user_id, email=email, role=role)
    except JWTError:
        raise err


def require_admin(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "FORBIDDEN", "message": "Requiere rol Admin."}},
        )
    return user
