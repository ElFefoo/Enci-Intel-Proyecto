"""
Repositorio de chat: gestión de sesiones y mensajes en Firestore.
Colecciones: chat_sessions / chat_messages
"""
import uuid
from datetime import datetime, timezone
from google.cloud import firestore
from app.schemas.chat import ChatSession, ChatMessage


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_or_create_session(
    db: firestore.AsyncClient,
    user_id: str,
    session_id: str | None,
    first_question: str,
) -> str:
    """
    Retorna el session_id a usar.
    Si session_id existe y pertenece al usuario, lo reutiliza.
    Si no, crea una sesión nueva.
    """
    if session_id:
        ref = db.collection("chat_sessions").document(session_id)
        doc = await ref.get()
        if doc.exists and doc.to_dict().get("user_id") == user_id:
            await ref.update({"updated_at": _now()})
            return session_id

    new_id = str(uuid.uuid4())
    title = first_question[:60] + ("..." if len(first_question) > 60 else "")
    await db.collection("chat_sessions").document(new_id).set({
        "id": new_id,
        "user_id": user_id,
        "title": title,
        "created_at": _now(),
        "updated_at": _now(),
        "message_count": 0,
    })
    return new_id


async def save_message(
    db: firestore.AsyncClient,
    session_id: str,
    user_id: str,
    role: str,
    content: str,
    species: str | None = None,
    category: str | None = None,
) -> str:
    """Persiste un mensaje en Firestore y actualiza el contador de sesión."""
    msg_id = str(uuid.uuid4())
    await db.collection("chat_messages").document(msg_id).set({
        "id": msg_id,
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "species": species,
        "category": category,
        "created_at": _now(),
    })
    # Actualiza contador en sesión
    session_ref = db.collection("chat_sessions").document(session_id)
    await session_ref.update({
        "message_count": firestore.Increment(1),
        "updated_at": _now(),
    })
    return msg_id


async def get_session_history(
    db: firestore.AsyncClient,
    session_id: str,
    user_id: str,
    limit: int = 20,
) -> list[dict]:
    """Retorna los últimos mensajes de una sesión para el historial de contexto."""
    query = (
        db.collection("chat_messages")
        .where("session_id", "==", session_id)
        .where("user_id", "==", user_id)
        .order_by("created_at", direction=firestore.Query.ASCENDING)
        .limit(limit)
    )
    docs = query.stream()
    messages = []
    async for doc in docs:
        messages.append(doc.to_dict())
    return messages


async def list_user_sessions(
    db: firestore.AsyncClient,
    user_id: str,
    limit: int = 20,
    cursor: str | None = None,
) -> tuple[list[dict], bool]:
    """Lista sesiones del usuario paginadas por cursor."""
    query = (
        db.collection("chat_sessions")
        .where("user_id", "==", user_id)
        .order_by("updated_at", direction=firestore.Query.DESCENDING)
        .limit(limit + 1)
    )
    if cursor:
        try:
            cursor_doc = await db.collection("chat_sessions").document(cursor).get()
            if cursor_doc.exists:
                query = query.start_after(cursor_doc)
        except Exception:
            pass

    docs = query.stream()
    sessions = []
    async for doc in docs:
        sessions.append(doc.to_dict())

    has_more = len(sessions) > limit
    return sessions[:limit], has_more


async def delete_user_history(
    db: firestore.AsyncClient,
    user_id: str,
) -> int:
    """Elimina todas las sesiones y mensajes del usuario. Retorna total eliminado."""
    # Eliminar mensajes
    msgs_query = db.collection("chat_messages").where("user_id", "==", user_id)
    msg_count = 0
    async for doc in msgs_query.stream():
        await doc.reference.delete()
        msg_count += 1

    # Eliminar sesiones
    sessions_query = db.collection("chat_sessions").where("user_id", "==", user_id)
    async for doc in sessions_query.stream():
        await doc.reference.delete()

    return msg_count
