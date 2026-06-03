"""
Agente: PriceBenchmarkAgent
Compara precios SKU entre Encipharm y la competencia.
Genera alertas PRICECHANGE cuando la variación supera el umbral configurado.

Fuentes: catálogos online Zoetis, Drag Pharma, Agrovet Market.
Frecuencia: configurable (por defecto continua / cada 6h).
"""
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from app.agents.base_agent import BaseAgent

# Competidores a monitorear — URL y parser a implementar por cada uno
COMPETITORS: dict[str, str] = {
    "zoetis": "https://www.zoetis.cl/productos",
    "dragpharma": "https://www.dragpharma.cl/productos",
    "agrovet": "https://www.agrovet.cl/catalogo",
}

DEFAULT_ALERT_THRESHOLD_PCT = 15.0  # % de variación mínima para emitir alerta


class PriceBenchmarkAgent(BaseAgent):
    def __init__(self, db):
        super().__init__("agent-price-benchmark", db)

    async def fetch(self) -> list[dict]:
        """Scraping de precios públicos de competidores."""
        results: list[dict] = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for competitor_id, url in COMPETITORS.items():
                try:
                    resp = await client.get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0 (compatible; EnciIntelBot/1.0)"},
                    )
                    resp.raise_for_status()
                    products = self._parse_prices(resp.text, competitor_id)
                    results.extend(products)
                    self.log.info("fetched_competitor", competitor=competitor_id, count=len(products))
                except Exception as e:
                    self.log.warning("fetch_competitor_failed", competitor=competitor_id, error=str(e))
        return results

    def _parse_prices(self, html: str, competitor_id: str) -> list[dict]:
        """
        Parser HTML por competidor.
        TODO: implementar selectores CSS específicos para cada sitio.
        Estructura esperada por producto:
          { sku, name, competitor_id, price, currency, url, capturedAt }
        """
        soup = BeautifulSoup(html, "lxml")
        products: list[dict] = []
        # Ejemplo genérico — reemplazar con selectores reales:
        # for card in soup.select(".product-card"):
        #     sku = card.get("data-sku", "")
        #     name = card.select_one(".product-name").get_text(strip=True)
        #     price_text = card.select_one(".price").get_text(strip=True)
        #     price = float(price_text.replace("$", "").replace(".", "").replace(",", "."))
        #     products.append({"sku": sku, "name": name, "competitor_id": competitor_id,
        #                       "price": price, "currency": "CLP", "capturedAt": datetime.now(timezone.utc).isoformat()})
        return products

    async def process(self, raw_data: list[dict]) -> list[dict]:
        """Cruza con precios anteriores en Firestore y calcula variación porcentual."""
        enriched: list[dict] = []
        for item in raw_data:
            doc_id = f"{item['competitor_id']}_{item['sku']}"
            prev_doc = self.db.collection("products").document(doc_id).get()
            if prev_doc.exists:
                prev = prev_doc.to_dict()
                old_price = prev.get("price", 0)
                if old_price and old_price > 0:
                    item["change_pct"] = round(((item["price"] - old_price) / old_price) * 100, 2)
                    item["old_price"] = old_price
            enriched.append(item)
        return enriched

    async def save(self, data: list[dict]) -> None:
        """Batch upsert de productos en Firestore."""
        if not data:
            return
        batch = self.db.batch()
        for product in data:
            doc_id = f"{product['competitor_id']}_{product['sku']}"
            ref = self.db.collection("products").document(doc_id)
            batch.set(ref, product, merge=True)
        batch.commit()

    async def generate_alerts(self, data: list[dict]) -> int:
        """Crea alertas PRICECHANGE si la variación supera el umbral."""
        # Leer umbral desde config del agente en Firestore (fallback al default)
        agent_doc = self.db.collection("agents").document(self.agent_id).get()
        threshold = DEFAULT_ALERT_THRESHOLD_PCT
        if agent_doc.exists:
            threshold = agent_doc.to_dict().get("config", {}).get("alertThresholdPct", threshold)

        count = 0
        for product in data:
            change = abs(product.get("change_pct", 0))
            if change >= threshold:
                priority = "high" if change >= 20 else "medium"
                self.db.collection("alerts").add({
                    "type": "PRICECHANGE",
                    "priority": priority,
                    "competitor": product["competitor_id"],
                    "product": product["name"],
                    "metadata": {
                        "sku": product["sku"],
                        "oldPrice": product.get("old_price"),
                        "newPrice": product["price"],
                        "changePct": product["change_pct"],
                        "currency": product.get("currency", "CLP"),
                    },
                    "read": False,
                    "agentId": self.agent_id,
                    "createdAt": datetime.now(timezone.utc),
                })
                count += 1
        return count
