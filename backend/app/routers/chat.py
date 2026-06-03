from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.middleware.auth import get_current_user
from app.services.firestore_service import get_db

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    sessionId: str | None = None


@router.post("/chat/message")
async def send_message(
    body: ChatMessage,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    POST /api/v1/chat/message
    Consultor Veterinario IA — powered by Vertex AI Gemini.
    """
    # TODO: integrar con Vertex AI (Gemini)
    return {
        "success": True,
        "data": {
            "sessionId": body.sessionId or "new-session",
            "response": "[Consultor IA no configurado aún. Pendiente integrar Vertex AI Gemini]",
            "sources": [],
        },
    }


@router.get("/chat/sessions")
async def list_sessions(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """GET /api/v1/chat/sessions"""
    return {"success": True, "data": []}
