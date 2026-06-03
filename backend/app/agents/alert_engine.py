from .base_agent import BaseAgent


class AlertEngineAgent(BaseAgent):
    """Motor de Alertas — consolida y prioriza salida de los 4 agentes anteriores."""

    def __init__(self, db):
        super().__init__("agent-alert-engine", db)

    async def fetch(self) -> list[dict]:
        # Lee alertas sin procesar de Firestore
        return []

    async def process(self, raw_data: list[dict]) -> list[dict]:
        # TODO: deduplicar, priorizar, enriquecer con contexto Gemini
        return raw_data

    async def save(self, data: list[dict]):
        pass

    async def generate_alerts(self, data: list[dict]):
        pass
