from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.services.firestore_service import get_db

router = APIRouter()


@router.get("/dashboard/summary")
async def get_summary(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    GET /api/v1/dashboard/summary
    Resumen general: KPIs, alertas recientes, estado agentes.
    """
    # TODO: implementar queries a Firestore
    return {
        "success": True,
        "data": {
            "kpis": {
                "activeAgents": 0,
                "unreadAlerts": 0,
                "marketSharePct": None,
                "criticalAlerts24h": 0,
            },
            "recentAlerts": [],
            "agentStatus": [],
        },
    }
