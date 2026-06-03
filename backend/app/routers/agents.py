from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.middleware.auth import get_current_user, require_role
from app.services.firestore_service import get_db

router = APIRouter()


class AgentConfigUpdate(BaseModel):
    competitors: list[str] | None = None
    alertThresholdPct: float | None = None
    keywords: list[str] | None = None
    notificationsEnabled: bool | None = None
    schedule: str | None = None


@router.get("/agents")
async def list_agents(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """GET /api/v1/agents"""
    # TODO: leer colección 'agents' de Firestore
    return {"success": True, "data": []}


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """GET /api/v1/agents/{id}"""
    doc = await db.collection("agents").document(agent_id).get()
    if not doc.exists:
        raise HTTPException(404, detail={"code": "AGENT_NOT_FOUND", "message": "Agente no encontrado"})
    return {"success": True, "data": {"id": doc.id, **doc.to_dict()}}


@router.post("/agents/{agent_id}/trigger")
async def trigger_agent(
    agent_id: str,
    user: dict = Depends(require_role("Admin")),
    db=Depends(get_db),
):
    """POST /api/v1/agents/{id}/trigger — Ejecutar agente manualmente."""
    # TODO: encolar en Cloud Tasks
    return {"success": True, "data": {"agentId": agent_id, "queued": True}}


@router.patch("/agents/{agent_id}/config")
async def update_config(
    agent_id: str,
    body: AgentConfigUpdate,
    user: dict = Depends(require_role("Admin")),
    db=Depends(get_db),
):
    """PATCH /api/v1/agents/{id}/config"""
    # TODO: actualizar config en Firestore
    return {"success": True, "data": {"agentId": agent_id, "config": body.model_dump(exclude_none=True)}}


@router.get("/agents/{agent_id}/runs")
async def get_runs(
    agent_id: str,
    limit: int = 10,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """GET /api/v1/agents/{id}/runs"""
    # TODO: query colección 'agentRuns' filtrado por agentId
    return {"success": True, "data": []}
