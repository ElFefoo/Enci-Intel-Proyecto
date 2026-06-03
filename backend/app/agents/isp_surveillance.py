from .base_agent import BaseAgent


class ISPSurveillanceAgent(BaseAgent):
    """Vigilancia ISP Chile — detecta nuevos registros de productos veterinarios."""

    def __init__(self, db):
        super().__init__("agent-isp-surveillance", db)

    async def fetch(self) -> list[dict]:
        # TODO: scrapear https://www.ispch.cl/farmacosvet
        return []

    async def process(self, raw_data: list[dict]) -> list[dict]:
        return raw_data

    async def save(self, data: list[dict]):
        pass

    async def generate_alerts(self, data: list[dict]):
        pass
