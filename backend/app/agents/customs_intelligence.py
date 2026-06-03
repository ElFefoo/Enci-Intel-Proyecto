from .base_agent import BaseAgent


class CustomsIntelligenceAgent(BaseAgent):
    """Inteligencia Aduanera — importaciones SAG + Aduanas cap. 30 / 2309."""

    def __init__(self, db):
        super().__init__("agent-customs-intelligence", db)

    async def fetch(self) -> list[dict]:
        # TODO: integrar API Aduanas Chile
        return []

    async def process(self, raw_data: list[dict]) -> list[dict]:
        return raw_data

    async def save(self, data: list[dict]):
        pass

    async def generate_alerts(self, data: list[dict]):
        pass
