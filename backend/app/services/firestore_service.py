"""
Cliente Firestore singleton.
En desarrollo local sin credenciales GCP, retorna un MockFirestoreClient
que no lanza errores y permite que el resto del sistema funcione.
"""
from functools import lru_cache
from app.config import get_settings


class MockFirestoreClient:
    """Cliente Firestore falso para desarrollo local sin credenciales GCP."""

    def collection(self, *args, **kwargs):
        return self

    def document(self, *args, **kwargs):
        return self

    async def get(self, *args, **kwargs):
        return MockDoc()

    async def set(self, *args, **kwargs):
        return None

    async def update(self, *args, **kwargs):
        return None

    async def delete(self, *args, **kwargs):
        return None

    def where(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def start_after(self, *args, **kwargs):
        return self

    def stream(self):
        return _empty_async_gen()


class MockDoc:
    exists = False

    def to_dict(self):
        return {}


async def _empty_async_gen():
    return
    yield  # hace que sea un async generator vacio


@lru_cache
def get_firestore():
    settings = get_settings()
    try:
        from google.cloud import firestore
        client = firestore.AsyncClient(project=settings.gcp_project_id)
        return client
    except Exception:
        # Sin credenciales GCP en local: usar cliente mock silencioso
        return MockFirestoreClient()
