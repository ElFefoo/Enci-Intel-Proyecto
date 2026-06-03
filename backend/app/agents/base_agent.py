from abc import ABC, abstractmethod
from datetime import datetime, timezone
from google.cloud import firestore
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Clase abstracta base para todos los agentes de Enci-Intel.
    Pipeline: fetch → process → save → generate_alerts
    """

    def __init__(self, agent_id: str, db: firestore.AsyncClient):
        self.agent_id = agent_id
        self.db = db
        self.logger = logging.getLogger(f"agent.{agent_id}")

    async def run(self):
        run_ref = await self._start_run()
        try:
            self.logger.info(f"[{self.agent_id}] Iniciando ejecución")
            raw_data = await self.fetch()
            processed = await self.process(raw_data)
            await self.save(processed)
            await self.generate_alerts(processed)
            await self._end_run(run_ref, status="success")
            self.logger.info(f"[{self.agent_id}] Ejecución exitosa")
        except Exception as e:
            self.logger.error(f"[{self.agent_id}] Error: {e}")
            await self._end_run(run_ref, status="error", error=str(e))
            raise

    @abstractmethod
    async def fetch(self) -> list[dict]:
        """Extrae datos de fuentes externas."""
        ...

    @abstractmethod
    async def process(self, raw_data: list[dict]) -> list[dict]:
        """Normaliza y enriquece los datos."""
        ...

    @abstractmethod
    async def save(self, data: list[dict]):
        """Persiste en Firestore."""
        ...

    @abstractmethod
    async def generate_alerts(self, data: list[dict]):
        """Genera alertas si se superan umbrales."""
        ...

    async def _start_run(self) -> firestore.AsyncDocumentReference:
        now = datetime.now(timezone.utc)
        run_data = {"agentId": self.agent_id, "startedAt": now, "status": "running"}
        _, run_ref = await self.db.collection("agentRuns").add(run_data)
        await self.db.collection("agents").document(self.agent_id).set(
            {"status": "running", "lastRunAt": now}, merge=True
        )
        return run_ref

    async def _end_run(self, run_ref, status: str, error: str | None = None):
        now = datetime.now(timezone.utc)
        update = {"status": status, "finishedAt": now}
        if error:
            update["error"] = error
        await run_ref.update(update)
        await self.db.collection("agents").document(self.agent_id).update(
            {"status": "idle" if status == "success" else "error", "lastRunStatus": status, "lastRunAt": now}
        )
