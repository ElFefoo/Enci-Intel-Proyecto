from fastapi import APIRouter, Depends
from app.middleware.auth import CurrentUser, get_current_user
from app.services.firestore_service import get_firestore

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    include_alerts: bool = True,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_firestore),
):
    """KPIs del panel principal — polling cada 60s."""
    # TODO: implementar con Firestore
    return {
        "success": True,
        "data": {
            "agents": {"total": 5, "running": 0, "waiting": 0, "idle": 5},
            "alerts": {"unreadCount": 0, "criticalCount": 0, "lastUpdated": None},
            "market": {"encipharmSharePct": 0.0, "trend": "stable", "period": "Q2-2026"},
            "recentAlerts": [],
        },
    }
