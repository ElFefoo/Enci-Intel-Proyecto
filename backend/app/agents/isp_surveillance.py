"""
Agente: IspSurveillanceAgent
Monitorea boletines y registros del ISP Chile (Instituto de Salud Pública).
Genera alertas NEWREGISTRATION cuando se registra un nuevo producto veterinario.

Fuentes: ISP Chile — buscador de registros sanitarios, boletín oficial.
Frecuencia: diaria.
"""
from app.agents.base_agent import BaseAgent


class IspSurveillanceAgent(BaseAgent):
    def __init__(self, db):
        super().__init__("agent-isp-surveillance", db)

    async def fetch(self) -> list[dict]:
        """
        TODO: implementar consulta a:
        - https://www.ispch.cl/buscador-registros-sanitarios/
        - Boletín oficial ISP (productos veterinarios cap. 28)
        Filtrar por registros con fecha >= última ejecución.
        """
        return []

    async def process(self, raw_data: list[dict]) -> list[dict]:
        """
        TODO:
        - Normalizar campos: titular, producto, principio_activo, fecha_registro
        - Cruzar con catálogo de competidores conocidos para identificar titular
        """
        return raw_data

    async def save(self, data: list[dict]) -> None:
        # TODO: batch write a colección 'isp_registrations'
        pass

    async def generate_alerts(self, data: list[dict]) -> int:
        # TODO: crear alerta NEWREGISTRATION por cada registro nuevo de competidor
        return 0
