"""
Router del Módulo Consultor Veterinario IA.
Endpoints:
  POST /api/v1/chat/query     -> streaming SSE
  GET  /api/v1/chat/history   -> historial del usuario
  DELETE /api/v1/chat/history -> eliminar historial
"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.config import get_settings
from app.services.gemini_service import stream_gemini_response
from app.services.firestore_service import get_firestore
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["Consultor IA"])
settings = get_settings()

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


async def _get_rate_count(user_id: str, db) -> int:
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        doc = await db.collection("rate_limits").document(f"{user_id}_{today}").get()
        return doc.to_dict().get("count", 0) if doc.exists else 0
    except Exception:
        return 0


async def _increment_rate_limit(user_id: str, db) -> None:
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ref = db.collection("rate_limits").document(f"{user_id}_{today}")
        doc = await ref.get()
        count = doc.to_dict().get("count", 0) if doc.exists else 0
        await ref.set({"user_id": user_id, "date": today, "count": count + 1})
    except Exception:
        pass


async def _get_recent_alerts(db) -> str:
    """Inyecta las 5 alertas más recientes como contexto de mercado en el prompt del LLM."""
    try:
        alerts = []
        query = db.collection("alerts").order_by("created_at", direction="DESCENDING").limit(5)
        async for doc in query.stream():
            d = doc.to_dict()
            alerts.append(
                f"- [{d.get('type', '')}] {d.get('title', '')} "
                f"({d.get('competitor', '')}): {d.get('body', '')}"
            )
        return "\n".join(alerts) if alerts else ""
    except Exception:
        return ""


async def _get_session_history(session_id: str, db) -> list[dict]:
    """Recupera historial de sesión para pasarlo como context window al LLM."""
    history = []
    try:
        query = (
            db.collection("chat_messages")
            .where("session_id", "==", session_id)
            .order_by("created_at")
            .limit(10)
        )
        async for doc in query.stream():
            d = doc.to_dict()
            history.append({"role": "user", "content": d["question"]})
            history.append({"role": "assistant", "content": d["answer"]})
    except Exception:
        pass
    return history


async def _save_message(
    user_id: str, session_id: str, message_id: str,
    request: ChatQueryRequest, full_answer: str, db
) -> None:
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
        pass


@router.post("/query")
async def chat_query(
    request: ChatQueryRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_firestore),
):
    user_id = current_user.get("uid", "dev-user")
    session_id = request.session_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    if not settings.disable_auth:
        count = await _get_rate_count(user_id, db)
        if count >= settings.chat_rate_limit_per_day:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Límite de {settings.chat_rate_limit_per_day} consultas/día alcanzado."
                }
            )

    history = await _get_session_history(session_id, db) if request.session_id else []
    alert_context = await _get_recent_alerts(db)

    full_answer: list[str] = []

    async def event_stream():
        async for event in stream_gemini_response(
            question=request.question,
            species=request.species,
            category=request.category,
            context=alert_context,
            history=history,
        ):
            if event.startswith("data: "):
                try:
                    parsed = json.loads(event[6:])
                    if parsed.get("type") == "token":
                        full_answer.append(parsed.get("content", ""))
                        yield event
                    elif parsed.get("type") == "done":
                        parsed["session_id"] = session_id
                        parsed["message_id"] = message_id
                        yield f"data: {json.dumps(parsed)}\n\n"
                        import asyncio
                        asyncio.create_task(_save_message(
                            user_id, session_id, message_id,
                            request, "".join(full_answer), db
                        ))
                        asyncio.create_task(_increment_rate_limit(user_id, db))
                        return
                    elif parsed.get("type") == "error":
                        yield event
                        return
                except Exception:
                    yield event
            else:
                yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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
        query = (
            db.collection("chat_messages")
            .where("user_id", "==", user_id)
            .order_by("created_at")
            .limit(min(limit, 100))
        )
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
    return {
        "success": True,
        "data": {"deleted_count": deleted, "deleted_at": datetime.now(timezone.utc).isoformat()}
    }
