from .base_agent import BaseAgent


class CompetitiveMonitoringAgent(BaseAgent):
    """Monitoreo Competitivo — LinkedIn + portales de noticias veterinarias."""

    def __init__(self, db):
        super().__init__("agent-competitive-monitoring", db)

    async def fetch(self) -> list[dict]:
        # TODO: RSS feeds + scraping noticias
        return []

    async def process(self, raw_data: list[dict]) -> list[dict]:
        return raw_data

    async def save(self, data: list[dict]):
        pass

    async def generate_alerts(self, data: list[dict]):
        pass
