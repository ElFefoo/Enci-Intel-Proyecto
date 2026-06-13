"""
Servicio Gemini / Vertex AI para el Consultor Veterinario IA.

MODO LOCAL: si USE_GEMINI_MOCK=true en .env, usa un generador local
que simula streaming sin necesitar credenciales de GCP.
En producción apunta a Vertex AI gemini-1.5-pro con streaming real.
"""
import json
import asyncio
from typing import AsyncGenerator

from app.config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# System prompt especializado en farmacologa veterinaria competitiva
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
Eres el Consultor Veterinario IA de Encipharm, empresa chilena líder en salud animal.
Tu rol es responder consultas técnicas sobre farmacología veterinaria, dosis, protocolos 
de tratamiento y comparativas de productos para el mercado chileno.

Directrices:
- Responde siempre en español.
- Basa tus respuestas en evidencia científica y fichas técnicas.
- Cuando sea relevante, compara productos Encipharm vs competencia (Zoetis, Drag Pharma, Agrovet, Virbac).
- Si el usuario especifica especie animal, enfoca la respuesta en esa especie.
- Si tienes contexto de alertas de mercado recientes, úsalo para enriquecer tu respuesta.
- Sé conciso pero completo. Usa bullet points para dosis y protocolos.
- Siempre aclara que las dosis deben ser validadas por un médico veterinario.
"""


def _build_prompt(question: str, species: str | None, category: str | None, context: str) -> str:
    parts = []
    if species:
        parts.append(f"Especie animal: {species}")
    if category:
        parts.append(f"Categoría terapéutica: {category}")
    if context:
        parts.append(f"Contexto de mercado reciente:\n{context}")
    parts.append(f"Consulta: {question}")
    return "\n".join(parts)


async def stream_gemini_response(
    question: str,
    species: str | None = None,
    category: str | None = None,
    context: str = "",
    history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Genera tokens SSE. Alterna entre mock local y Vertex AI real
    según la variable USE_GEMINI_MOCK en .env.
    """
    use_mock = getattr(settings, "use_gemini_mock", True)

    if use_mock:
        async for event in _mock_stream(question, species, category):
            yield event
    else:
        async for event in _vertex_stream(question, species, category, context, history):
            yield event


async def _mock_stream(
    question: str,
    species: str | None,
    category: str | None,
) -> AsyncGenerator[str, None]:
    """Generador mock que simula respuesta de Gemini para desarrollo local."""
    especie_txt = f" para {species}" if species else ""
    categoria_txt = f" en categoría {category}" if category else ""

    respuesta = (
        f"**[MOCK Consultor Vet IA]** — Respuesta simulada{especie_txt}{categoria_txt}\n\n"
        f"📋 **Consulta recibida:** {question}\n\n"
        "🔬 **Información técnica (simulada):**\n"
        "- Principio activo: Enrofloxacina 10%\n"
        "- Dosis estándar: 5 mg/kg/día vía subcutánea\n"
        "- Duración tratamiento: 3-5 días\n"
        "- Esperar 14 días antes del sacrificio\n\n"
        "⚠️ *Validar siempre con médico veterinario. Este es un entorno de desarrollo local.*"
    )

    words = respuesta.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        payload = json.dumps({"type": "token", "content": chunk})
        yield f"data: {payload}\n\n"
        await asyncio.sleep(0.03)

    done_payload = json.dumps({
        "type": "done",
        "context_sources": 0,
        "session_id": "mock-session",
    })
    yield f"data: {done_payload}\n\n"


async def _vertex_stream(
    question: str,
    species: str | None,
    category: str | None,
    context: str,
    history: list[dict] | None,
) -> AsyncGenerator[str, None]:
    """Streaming real desde Vertex AI Gemini."""
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, Content, Part

        vertexai.init(
            project=settings.gcp_project_id,
            location=settings.vertex_ai_location,
        )
        model = GenerativeModel(
            model_name=settings.vertex_ai_model,
            system_instruction=SYSTEM_PROMPT,
        )

        prompt = _build_prompt(question, species, category, context)

        chat_history = []
        if history:
            for msg in history[-10:]:  # últimos 10 mensajes de contexto
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append(Content(role=role, parts=[Part.from_text(msg["content"])]))

        chat = model.start_chat(history=chat_history)
        responses = chat.send_message(prompt, stream=True)

        for response in responses:
            if response.text:
                payload = json.dumps({"type": "token", "content": response.text})
                yield f"data: {payload}\n\n"
                await asyncio.sleep(0)  # cede el event loop

        done_payload = json.dumps({
            "type": "done",
            "context_sources": 1 if context else 0,
        })
        yield f"data: {done_payload}\n\n"

    except Exception as e:
        error_payload = json.dumps({"type": "error", "message": str(e)})
        yield f"data: {error_payload}\n\n"
