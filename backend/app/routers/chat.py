"""
Router del Módulo Consultor Veterinario IA.
Endpoints:
  POST /api/v1/chat/query   → streaming SSE
  GET  /api/v1/chat/history → historial del usuario
  DELETE /api/v1/chat/history → eliminar historial
"""
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.config import get_settings
from app.services.gemini_service import stream_gemini_response
from app.services.firestore_service import get_firestore
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["Consultor IA"])
settings = get_settings()

# Valores válidos de species alineados con la spec
SPECIES_VALUES = {"aves", "porcinos", "rumiantes", "peces", "caninos", "felinos", "equinos"}


class ChatQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    species: str | None = Field(default=None)
    category: str | None = Field(default=None)
    session_id: str | None = Field(default=None)

    @field_validator("species")
    @classmethod
    def validate_species(cls, v: str | None) -> str | None:
        if v and v not in SPECIES_VALUES:
            raise ValueError(f"species inválido. Valores permitidos: {', '.join(sorted(SPECIES_VALUES))}")
        return v


async def _check_rate_limit(user_id: str, db) -> None:
    """Verifica que el usuario no supere 50 consultas/día."""
    if getattr(settings, "disable_auth", False):
        return  # Sin límite en desarrollo local
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        doc_ref = db.collection("rate_limits").document(f"{user_id}_{today}")
        doc = await doc_ref.get()
        count = doc.to_dict().get("count", 0) if doc.exists else 0
        limit = settings.chat_rate_limit_per_day
        if count >= limit:
            raise HTTPException(
                status_code=429,
                detail={"code": "RATE_LIMIT_EXCEEDED", "message": f"Límite de {limit} consultas/día alcanzado."}
            )
    except HTTPException:
        raise
    except Exception:
        pass  # Si Firestore falla, no bloqueamos al usuario


async def _increment_rate_limit(user_id: str, db) -> None:
    """Incrementa el contador de consultas del día."""
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        doc_ref = db.collection("rate_limits").document(f"{user_id}_{today}")
        doc = await doc_ref.get()
        count = doc.to_dict().get("count", 0) if doc.exists else 0
        await doc_ref.set({"user_id": user_id, "date": today, "count": count + 1})
    except Exception:
        pass


async def _save_message(user_id: str, session_id: str, message_id: str,
                        request: ChatQueryRequest, full_answer: str, db) -> None:
    """Persiste el mensaje en Firestore."""
    try:
        await db.collection("chat_messages").document(message_id).set({
            "id": message_id,
            "user_id": user_id,
            "session_id": session_id,
            "question": request.question,
            "answer": full_answer,
            "species": request.species,
            "category": request.category,
            "sources": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass  # Firestore mock en local — no bloquear


@router.post("/query")
async def chat_query(
    request: ChatQueryRequest,
    req: Request,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_firestore),
):
    user_id = current_user.get("uid", "dev-user")
    session_id = request.session_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    await _check_rate_limit(user_id, db)

    # Obtener historial de sesión para contexto
    history: list[dict] = []
    if request.session_id:
        try:
            msgs = db.collection("chat_messages") \
                .where("session_id", "==", request.session_id) \
                .order_by("created_at") \
                .limit(10)
            async for doc in msgs.stream():
                d = doc.to_dict()
                history.append({"role": "user", "content": d["question"]})
                history.append({"role": "assistant", "content": d["answer"]})
        except Exception:
            pass

    full_answer: list[str] = []

    async def event_stream():
        async for event in stream_gemini_response(
            question=request.question,
            species=request.species,
            category=request.category,
            context="",
            history=history,
        ):
            # Acumular respuesta para persistir al final
            if event.startswith("data: "):
                try:
                    import json as _json
                    parsed = _json.loads(event[6:])
                    if parsed.get("type") == "token":
                        full_answer.append(parsed.get("content", ""))
                    elif parsed.get("type") == "done":
                        # Agregar session_id y message_id al evento done
                        parsed["session_id"] = session_id
                        parsed["message_id"] = message_id
                        yield f"data: {_json.dumps(parsed)}\n\n"
                        # Persistir en Firestore (no bloquea el stream)
                        import asyncio
                        asyncio.create_task(_save_message(
                            user_id, session_id, message_id,
                            request, "".join(full_answer), db
                        ))
                        asyncio.create_task(_increment_rate_limit(user_id, db))
                        return
                except Exception:
                    pass
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history")
async def get_chat_history(
    limit: int = 20,
    cursor: str | None = None,
    species: str | None = None,
    session_id: str | None = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_firestore),
):
    user_id = current_user.get("uid", "dev-user")
    try:
        query = db.collection("chat_messages") \
            .where("user_id", "==", user_id) \
            .order_by("created_at") \
            .limit(min(limit, 100))
        if species:
            query = query.where("species", "==", species)
        if session_id:
            query = query.where("session_id", "==", session_id)

        messages = []
        async for doc in query.stream():
            messages.append(doc.to_dict())

        return {"success": True, "data": messages, "meta": {"total": len(messages), "has_more": False}}
    except Exception:
        return {"success": True, "data": [], "meta": {"total": 0, "has_more": False}}


@router.delete("/history")
async def delete_chat_history(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_firestore),
):
    user_id = current_user.get("uid", "dev-user")
    deleted = 0
    try:
        async for doc in db.collection("chat_messages").where("user_id", "==", user_id).stream():
            await doc.reference.delete()
            deleted += 1
    except Exception:
        pass
    return {"success": True, "data": {"deleted_count": deleted, "deleted_at": datetime.now(timezone.utc).isoformat()}}
