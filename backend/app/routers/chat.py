from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.middleware.auth import CurrentUser, get_current_user
from app.services.firestore_service import get_firestore

router = APIRouter()

class ChatQuery(BaseModel):
    query: str
    species: Optional[str] = None
    category: Optional[str] = None
    session_id: Optional[str] = None

@router.post("/chat/query")
async def chat_query(body: ChatQuery, user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    """Consultor Veterinario IA — Streaming SSE con Gemini."""
    async def generate():
        # TODO: integrar Vertex AI Gemini con streaming real
        yield 'data: {"token": "Consultor Vet IA listo para integración Gemini"}\n\n'
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/chat/history")
async def get_chat_history(session_id: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    return {"success": True, "data": []}

@router.delete("/chat/history")
async def clear_chat_history(user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    return {"success": True, "data": {"deleted": True}}
