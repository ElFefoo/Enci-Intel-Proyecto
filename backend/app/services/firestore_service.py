"""Singleton cliente Firestore."""
from functools import lru_cache
from google.cloud import firestore
from app.config import get_settings

@lru_cache
def get_firestore() -> firestore.AsyncClient:
    settings = get_settings()
    return firestore.AsyncClient(project=settings.gcp_project_id)
