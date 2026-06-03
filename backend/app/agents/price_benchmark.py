import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from .base_agent import BaseAgent

# Competidores a monitorear — expandir con parsers reales
COMPETITORS: dict[str, str] = {
    "zoetis":    "https://www.zoetis.cl/productos",
    "dragpharma": "https://www.dragpharma.cl/productos",
    "agrovet":   "https://www.agrovet.cl/catalogo",
}

DEFAULT_THRESHOLD_PCT = 15.0


class PriceBenchmarkAgent(BaseAgent):
    def __init__(self, db):
        super().__init__("agent-price-benchmark", db)

    async def fetch(self) -> list[dict]:
        results = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for competitor_id, url in COMPETITORS.items():
                try:
                    resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                    resp.raise_for_status()
                    products = self._parse(resp.text, competitor_id)
                    results.extend(products)
                    self.logger.info(f"[{competitor_id}] {len(products)} productos extraídos")
                except Exception as e:
                    self.logger.warning(f"[{competitor_id}] Fallo scraping: {e}")
        return results

    def _parse(self, html: str, competitor_id: str) -> list[dict]:
        """
        TODO: implementar parser específico por competidor.
        Cada parser debe retornar lista de dicts con:
        { sku, name, price, currency, category, activeIngredient }
        """
        soup = BeautifulSoup(html, "lxml")
        # Placeholder — reemplazar con selector real de cada sitio
        return []

    async def process(self, raw_data: list[dict]) -> list[dict]:
        """Cruza con precios previos y calcula variación porcentual."""
        enriched = []
        for item in raw_data:
            doc = await self.db.collection("products").document(item["sku"]).get()
            if doc.exists:
                old_price = doc.to_dict().get("price", 0)
                if old_price and old_price > 0:
                    item["changePct"] = round(((item["price"] - old_price) / old_price) * 100, 2)
                    item["oldPrice"] = old_price
            item["updatedAt"] = datetime.now(timezone.utc)
            enriched.append(item)
        return enriched

    async def save(self, data: list[dict]):
        """Batch write a colección 'products'."""
        batch = self.db.batch()
        for product in data:
            ref = self.db.collection("products").document(product["sku"])
            batch.set(ref, product, merge=True)
        await batch.commit()

    async def generate_alerts(self, data: list[dict]):
        threshold = DEFAULT_THRESHOLD_PCT
        # Leer umbral configurado en Firestore si existe
        config_doc = await self.db.collection("agents").document(self.agent_id).get()
        if config_doc.exists:
            threshold = config_doc.to_dict().get("config", {}).get("alertThresholdPct", threshold)

        for product in data:
            change = abs(product.get("changePct", 0))
            if change >= threshold:
                priority = "high" if change >= 20 else "medium"
                await self.db.collection("alerts").add({
                    "type": "PRICECHANGE",
                    "priority": priority,
                    "title": f"Cambio de precio: {product['name']}",
                    "body": f"{product['competitor']} modificó el precio de {product['name']} en {product['changePct']:+.1f}%",
                    "competitor": product["competitor"],
                    "product": product["name"],
                    "metadata": {
                        "sku": product["sku"],
                        "oldPrice": product.get("oldPrice"),
                        "newPrice": product["price"],
                        "changePct": product.get("changePct"),
                        "currency": product.get("currency", "CLP"),
                    },
                    "read": False,
                    "agentId": self.agent_id,
                    "createdAt": datetime.now(timezone.utc),
                })
