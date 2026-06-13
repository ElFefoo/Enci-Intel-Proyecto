"""Schemas Pydantic para el módulo Consultor Veterinario IA."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


SPECIES_VALID = {"bovino", "porcino", "aviar", "canino", "felino", "equino"}


class ChatQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Consulta veterinaria en texto libre")
    species: Optional[Literal["bovino", "porcino", "aviar", "canino", "felino", "equino"]] = None
    category: Optional[str] = None
    session_id: Optional[str] = None


class ChatMessage(BaseModel):
    id: str
    session_id: str
    user_id: str
    role: Literal["user", "assistant"]
    content: str
    species: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime


class ChatSession(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ChatHistoryResponse(BaseModel):
    success: bool = True
    data: list[ChatSession]
    meta: dict


class ChatMessagesResponse(BaseModel):
    success: bool = True
    data: list[ChatMessage]
    meta: dict
