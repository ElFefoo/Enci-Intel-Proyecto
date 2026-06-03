"""Endpoints internos — solo invocados por Cloud Tasks."""
from fastapi import APIRouter, Header, HTTPException, Depends
from app.services.firestore_service import get_firestore

router = APIRouter()

@router.post("/agents/run")
async def run_agent(agent_id: str, x_cloudtasks_taskname: str = Header(default=None), db=Depends(get_firestore)):
    if x_cloudtasks_taskname is None:
        raise HTTPException(403, detail="Solo accesible desde Cloud Tasks")
    # TODO: from app.agents import AGENT_MAP; await AGENT_MAP[agent_id](db).run()
    return {"success": True, "data": {"agentId": agent_id, "status": "queued"}}
