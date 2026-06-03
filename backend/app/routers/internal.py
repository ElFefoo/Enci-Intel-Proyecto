from fastapi import APIRouter, Header, HTTPException, Depends
from app.config import get_settings
from app.services.firestore_service import get_db

router = APIRouter(prefix="/internal")
settings = get_settings()

# Mapa de agentes registrados
AGENT_MAP: dict = {
    # "agent-price-benchmark": PriceBenchmarkAgent,  # se agregarán uno a uno
}


def _verify_internal(x_internal_secret: str = Header(...)):
    if x_internal_secret != settings.INTERNAL_API_SECRET:
        raise HTTPException(401, detail="No autorizado")


@router.post("/agents/run")
async def run_agent(
    agent_id: str,
    _: None = Depends(_verify_internal),
    db=Depends(get_db),
):
    """
    POST /internal/agents/run?agent_id=...
    Invocado por Cloud Tasks para ejecutar un agente.
    """
    AgentClass = AGENT_MAP.get(agent_id)
    if not AgentClass:
        raise HTTPException(404, detail=f"Agente '{agent_id}' no encontrado")
    agent = AgentClass(db)
    await agent.run()
    return {"success": True, "data": {"agentId": agent_id}}
