from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.services.firestore_service import get_db

router = APIRouter()


@router.get("/market/map")
async def get_market_map(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """GET /api/v1/market/map — Datos para visualización del mapa competitivo."""
    return {"success": True, "data": {"competitors": [], "marketShare": {}}}


@router.get("/market/competitors")
async def list_competitors(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """GET /api/v1/market/competitors"""
    return {"success": True, "data": []}
