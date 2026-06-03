from google.cloud import firestore
from functools import lru_cache
from app.config import get_settings

settings = get_settings()


@lru_cache
def get_db() -> firestore.AsyncClient:
    return firestore.AsyncClient(project=settings.GCP_PROJECT_ID)
