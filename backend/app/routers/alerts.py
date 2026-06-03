from fastapi import APIRouter, Depends, Query
from app.middleware.auth import get_current_user
from app.services.firestore_service import get_db

router = APIRouter()


@router.get("/alerts")
async def list_alerts(
    type: str | None = Query(None),
    priority: str | None = Query(None),
    competitor: str | None = Query(None),
    read: bool | None = Query(None),
    limit: int = Query(20, le=100),
    cursor: str | None = Query(None),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """GET /api/v1/alerts — Lista de alertas con filtros y paginación."""
    # TODO: query Firestore collection 'alerts'
    return {"success": True, "data": [], "meta": {"total": 0, "hasMore": False, "nextCursor": None}}


@router.patch("/alerts/{alert_id}/read")
async def mark_read(
    alert_id: str,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """PATCH /api/v1/alerts/{id}/read"""
    # TODO: actualizar campo 'read' en Firestore
    return {"success": True, "data": {"alertId": alert_id, "read": True}}


@router.patch("/alerts/read-all")
async def mark_all_read(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """PATCH /api/v1/alerts/read-all"""
    return {"success": True, "data": {"updated": 0}}
