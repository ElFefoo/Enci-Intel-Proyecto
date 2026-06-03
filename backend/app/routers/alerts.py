from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.middleware.auth import CurrentUser, get_current_user
from app.services.firestore_service import get_firestore

router = APIRouter()

@router.get("/alerts")
async def list_alerts(
    limit: int = Query(20, le=100),
    cursor: Optional[str] = None,
    since: Optional[str] = None,
    type: Optional[str] = None,
    priority: Optional[str] = None,
    read: Optional[bool] = None,
    competitor: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_firestore),
):
    # TODO: query Firestore con filtros y cursor
    return {"success": True, "data": [], "meta": {"total": 0, "limit": limit, "nextCursor": None, "hasMore": False}}

@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: str, user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    return {"success": True, "data": {}}

@router.patch("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str, user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    return {"success": True, "data": {"id": alert_id, "read": True}}

@router.post("/alerts/mark-all-read")
async def mark_all_read(user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    return {"success": True, "data": {"updatedCount": 0}}
