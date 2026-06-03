"""Clase base abstracta para todos los agentes de Enci-Intel."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import structlog

logger = structlog.get_logger()


class BaseAgent(ABC):
    def __init__(self, agent_id: str, db):
        self.agent_id = agent_id
        self.db = db
        self.log = logger.bind(agent_id=agent_id)

    async def run(self):
        """Pipeline: fetch → process → save → generate_alerts"""
        run_ref = await self._start_run()
        try:
            self.log.info("agent_started")
            raw_data = await self.fetch()
            self.log.info("agent_fetched", count=len(raw_data))
            processed = await self.process(raw_data)
            await self.save(processed)
            alerts_count = await self.generate_alerts(processed)
            self.log.info("agent_completed", alerts_generated=alerts_count)
            await self._end_run(run_ref, status="success", alertsGenerated=alerts_count)
            return {"status": "success", "alertsGenerated": alerts_count}
        except Exception as e:
            self.log.error("agent_error", error=str(e))
            await self._end_run(run_ref, status="error", error=str(e))
            raise

    @abstractmethod
    async def fetch(self) -> list[dict]: ...

    @abstractmethod
    async def process(self, raw_data: list[dict]) -> list[dict]: ...

    @abstractmethod
    async def save(self, data: list[dict]) -> None: ...

    @abstractmethod
    async def generate_alerts(self, data: list[dict]) -> int: ...

    async def _start_run(self):
        now = datetime.now(timezone.utc)
        _, run_ref = self.db.collection("agentRuns").add(
            {"agentId": self.agent_id, "startedAt": now, "status": "running"}
        )
        self.db.collection("agents").document(self.agent_id).set(
            {"status": "running", "lastRunAt": now}, merge=True
        )
        return run_ref

    async def _end_run(self, run_ref, status: str, **kwargs):
        now = datetime.now(timezone.utc)
        run_ref.update({"status": status, "finishedAt": now, **kwargs})
        self.db.collection("agents").document(self.agent_id).set(
            {
                "status": "idle" if status == "success" else "error",
                "lastRunStatus": status,
                "lastRunFinishedAt": now,
            },
            merge=True,
        )
