"""
Agente: AlertEngineAgent
Consolida la salida de los 4 agentes de extracción y prioriza alertas.

Responsabilidades:
- Deduplicar alertas similares en ventana de 24h
- Recalcular prioridad según reglas de negocio (segmento, competidor, umbral)
- Emitir alerta STOCKOUT basada en ausencia de datos de precio por N días
- Notificar a usuarios via FCM/email (futuro)

Frecuencia: reactivo (invocado al terminar cada agente extractor) + cron cada 4h.
"""
from app.agents.base_agent import BaseAgent


class AlertEngineAgent(BaseAgent):
    def __init__(self, db):
        super().__init__("agent-alert-engine", db)

    async def fetch(self) -> list[dict]:
        """
        TODO: leer alertas recientes (< 24h) con status='pending' desde Firestore.
        """
        return []

    async def process(self, raw_data: list[dict]) -> list[dict]:
        """
        TODO:
        - Deduplicar por (type, competitor, sku) en ventana 24h
        - Aplicar reglas de prioridad según configuración de Admin
        - Detectar STOCKOUT: producto sin dato de precio por > N días
        """
        return raw_data

    async def save(self, data: list[dict]) -> None:
        # TODO: actualizar prioridad y marcar duplicados en Firestore
        pass

    async def generate_alerts(self, data: list[dict]) -> int:
        # TODO: emitir alertas STOCKOUT y notificaciones push
        return 0
