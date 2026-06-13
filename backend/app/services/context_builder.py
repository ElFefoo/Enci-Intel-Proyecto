"""
Constructor de contexto dinámico para el Consultor Veterinario IA.
Inyecta las últimas alertas y productos relevantes de Firestore
en el prompt de Gemini para respuestas con inteligencia de mercado.
"""
from google.cloud import firestore


async def build_market_context(
    db: firestore.AsyncClient,
    species: str | None = None,
    category: str | None = None,
    limit: int = 10,
) -> str:
    """
    Recupera las últimas N alertas de Firestore y las formatea
    como contexto de texto para el prompt de Gemini.
    Retorna string vacío si Firestore no está disponible.
    """
    try:
        query = db.collection("alerts").order_by(
            "created_at", direction=firestore.Query.DESCENDING
        ).limit(limit)

        docs = query.stream()
        alerts = []
        async for doc in docs:
            data = doc.to_dict()
            alerts.append(data)

        if not alerts:
            return ""

        lines = ["=== Alertas de mercado recientes ==="]
        for alert in alerts:
            competitor = alert.get("competitor", "desconocido").title()
            product = alert.get("product", "N/A")
            alert_type = alert.get("type", "")
            title = alert.get("title", "")
            priority = alert.get("priority", "medium")
            lines.append(f"[{priority.upper()}] {competitor} - {product}: {title} (tipo: {alert_type})")

        return "\n".join(lines)

    except Exception:
        # En local sin Firestore real, retorna contexto vacío sin lanzar error
        return ""
