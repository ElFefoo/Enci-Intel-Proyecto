"""
Router: Consultor Veterinario IA
Endpoints:
  POST /api/v1/chat/query       — chat SSE con Gemini
  GET  /api/v1/chat/history     — lista sesiones del usuario
  GET  /api/v1/chat/sessions/{session_id}/messages — mensajes de sesión
  DELETE /api/v1/chat/history   — borra historial del usuario
"""
import json
from typing import Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.middleware.auth import CurrentUser, get_current_user
from app.services.firestore_service import get_firestore
from app.services.gemini_service import stream_gemini_response
from app.services.context_builder import build_market_context
from app.services.chat_repository import (
    get_or_create_session,
    save_message,
    get_session_history,
    list_user_sessions,
    delete_user_history,
)
from app.schemas.chat import ChatQueryRequest

router = APIRouter()


@router.post("/chat/query", summary="Consultor Vet IA — Streaming SSE")
async def chat_query(
    body: ChatQueryRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db=Depends(get_firestore),
):
    """
    Recibe una pregunta veterinaria y responde con streaming SSE token a token.
    - Crea o reutiliza sesión de conversación.
    - Inyecta contexto de alertas recientes de Firestore.
    - Persiste pregunta y respuesta completa en Firestore.
    """
    if len(body.question) > 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {"code": "QUESTION_TOO_LONG", "message": "La pregunta supera los 2000 caracteres."}},
        )

    async def generate():
        # 1. Obtener o crear sesión
        try:
            session_id = await get_or_create_session(
                db, user.user_id, body.session_id, body.question
            )
        except Exception:
            session_id = body.session_id or "local-session"

        # 2. Guardar mensaje del usuario
        try:
            await save_message(
                db, session_id, user.user_id,
                role="user",
                content=body.question,
                species=body.species,
                category=body.category,
            )
        except Exception:
            pass

        # 3. Obtener historial de contexto
        try:
            history = await get_session_history(db, session_id, user.user_id)
        except Exception:
            history = []

        # 4. Construir contexto de mercado desde alertas
        try:
            context = await build_market_context(db, body.species, body.category)
        except Exception:
            context = ""

        # 5. Stream de Gemini token a token
        full_response = []
        async for event in stream_gemini_response(
            question=body.question,
            species=body.species,
            category=body.category,
            context=context,
            history=history,
        ):
            # Capturar tokens para persistir al final
            try:
                parsed = json.loads(event.replace("data: ", "").strip())
                if parsed.get("type") == "token":
                    full_response.append(parsed.get("content", ""))
                elif parsed.get("type") == "done":
                    # Enriquecer el evento done con session_id real
                    parsed["session_id"] = session_id
                    event = f"data: {json.dumps(parsed)}\n\n"
            except Exception:
                pass
            yield event

        # 6. Persistir respuesta completa del asistente
        if full_response:
            try:
                await save_message(
                    db, session_id, user.user_id,
                    role="assistant",
                    content="".join(full_response),
                    species=body.species,
                    category=body.category,
                )
            except Exception:
                pass

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/history", summary="Lista sesiones del usuario")
async def get_chat_history(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db=Depends(get_firestore),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
):
    """Retorna las sesiones de conversación del usuario paginadas."""
    try:
        sessions, has_more = await list_user_sessions(db, user.user_id, limit, cursor)
        next_cursor = sessions[-1]["id"] if has_more and sessions else None
        return {
            "success": True,
            "data": sessions,
            "meta": {"limit": limit, "has_more": has_more, "next_cursor": next_cursor},
        }
    except Exception as e:
        return {"success": True, "data": [], "meta": {"limit": limit, "has_more": False, "next_cursor": None}}


@router.get("/chat/sessions/{session_id}/messages", summary="Mensajes de una sesión")
async def get_session_messages(
    session_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db=Depends(get_firestore),
    limit: int = Query(default=50, ge=1, le=100),
):
    """Retorna los mensajes de una sesión específica del usuario."""
    try:
        messages = await get_session_history(db, session_id, user.user_id, limit)
        return {
            "success": True,
            "data": messages,
            "meta": {"session_id": session_id, "count": len(messages)},
        }
    except Exception:
        return {"success": True, "data": [], "meta": {"session_id": session_id, "count": 0}}


@router.delete("/chat/history", summary="Borra historial completo del usuario")
async def clear_chat_history(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db=Depends(get_firestore),
):
    """Elimina permanentemente todas las sesiones y mensajes del usuario autenticado."""
    try:
        deleted_count = await delete_user_history(db, user.user_id)
        return {"success": True, "data": {"deleted_count": deleted_count}}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )
