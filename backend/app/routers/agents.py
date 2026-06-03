from fastapi import APIRouter, Depends
from app.middleware.auth import CurrentUser, get_current_user, require_admin
from app.services.firestore_service import get_firestore

router = APIRouter()

@router.get("/agents")
async def list_agents(user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    """Estado en tiempo real de los 5 agentes."""
    return {"success": True, "data": []}

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    return {"success": True, "data": {}}

@router.put("/agents/{agent_id}/config")
async def update_agent_config(
    agent_id: str, config: dict,
    user: CurrentUser = Depends(require_admin),
    db=Depends(get_firestore),
):
    """Solo Admin puede modificar configuración."""
    return {"success": True, "data": {"id": agent_id, "config": config}}

@router.get("/agents/{agent_id}/logs")
async def get_agent_logs(
    agent_id: str, limit: int = 10,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_firestore),
):
    return {"success": True, "data": []}
