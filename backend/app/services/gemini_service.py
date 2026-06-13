"""
Servicio Gemini para el Consultor Veterinario IA.

Tres modos configurables via .env:

  GEMINI_MODE=mock      → respuesta hardcodeada, sin API, sin costo (default local)
  GEMINI_MODE=api_key   → Gemini API con API Key de Google AI Studio (GRATIS con free tier)
  GEMINI_MODE=vertex    → Vertex AI con credenciales GCP (producción)

Para modo api_key, obtener key en: https://aistudio.google.com/app/apikey
"""
import json
import asyncio
from typing import AsyncGenerator

from app.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """\
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
    Punto de entrada único. Despacha al modo correcto según GEMINI_MODE en .env.
    """
    mode = getattr(settings, "gemini_mode", "mock").lower()

    if mode == "api_key":
        async for event in _api_key_stream(question, species, category, context, history):
            yield event
    elif mode == "vertex":
        async for event in _vertex_stream(question, species, category, context, history):
            yield event
    else:  # mock (default)
        async for event in _mock_stream(question, species, category):
            yield event


# ---------------------------------------------------------------------------
# MODO 1: Mock local — sin API, sin costo
# ---------------------------------------------------------------------------
async def _mock_stream(
    question: str,
    species: str | None,
    category: str | None,
) -> AsyncGenerator[str, None]:
    """Generador hardcodeado para desarrollo local sin ninguna API."""
    especie_txt = f" para {species}" if species else ""
    categoria_txt = f" en categoría {category}" if category else ""

    respuesta = (
        f"**[MOCK Consultor Vet IA]** — Respuesta simulada{especie_txt}{categoria_txt}\n\n"
        f"📋 **Consulta recibida:** {question}\n\n"
        "🔬 **Información técnica (simulada, siempre igual):**\n"
        "- Principio activo: Enrofloxacina 10%\n"
        "- Dosis estándar: 5 mg/kg/día vía subcutánea\n"
        "- Duración tratamiento: 3-5 días\n"
        "- Esperar 14 días antes del sacrificio\n\n"
        "⚠️ *Entorno mock — activar GEMINI_MODE=api_key para respuestas reales.*"
    )

    for i, word in enumerate(respuesta.split(" ")):
        chunk = word + (" " if i < len(respuesta.split(" ")) - 1 else "")
        yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        await asyncio.sleep(0.03)

    yield f"data: {json.dumps({'type': 'done', 'context_sources': 0, 'session_id': 'mock-session'})}\n\n"


# ---------------------------------------------------------------------------
# MODO 2: Gemini API Key — Google AI Studio, free tier generoso
# Requiere: pip install google-generativeai
# API Key en: https://aistudio.google.com/app/apikey
# ---------------------------------------------------------------------------
async def _api_key_stream(
    question: str,
    species: str | None,
    category: str | None,
    context: str,
    history: list[dict] | None,
) -> AsyncGenerator[str, None]:
    """Streaming con Gemini API Key (google-generativeai). Gratis en free tier."""
    try:
        import google.generativeai as genai

        api_key = getattr(settings, "gemini_api_key", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada en .env")

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=getattr(settings, "gemini_api_model", "gemini-1.5-flash"),
            system_instruction=SYSTEM_PROMPT,
        )

        # Construir historial de chat en formato google-generativeai
        chat_history = []
        if history:
            for msg in history[-10:]:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=chat_history)
        prompt = _build_prompt(question, species, category, context)

        # send_message con stream=True devuelve un iterador síncrono
        # lo envolvemos en un thread para no bloquear el event loop
        loop = asyncio.get_event_loop()
        response_iter = await loop.run_in_executor(
            None,
            lambda: chat.send_message(prompt, stream=True),
        )

        for chunk in response_iter:
            if chunk.text:
                payload = json.dumps({"type": "token", "content": chunk.text})
                yield f"data: {payload}\n\n"
                await asyncio.sleep(0)  # cede el event loop entre chunks

        done_payload = json.dumps({
            "type": "done",
            "context_sources": 1 if context else 0,
        })
        yield f"data: {done_payload}\n\n"

    except Exception as e:
        error_payload = json.dumps({"type": "error", "message": str(e)})
        yield f"data: {error_payload}\n\n"


# ---------------------------------------------------------------------------
# MODO 3: Vertex AI — producción GCP (de pago)
# Requiere: google-cloud-aiplatform + Application Default Credentials
# ---------------------------------------------------------------------------
async def _vertex_stream(
    question: str,
    species: str | None,
    category: str | None,
    context: str,
    history: list[dict] | None,
) -> AsyncGenerator[str, None]:
    """Streaming real desde Vertex AI Gemini. Requiere credenciales GCP."""
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
            for msg in history[-10:]:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append(Content(role=role, parts=[Part.from_text(msg["content"])]))

        chat = model.start_chat(history=chat_history)
        responses = chat.send_message(prompt, stream=True)

        for response in responses:
            if response.text:
                payload = json.dumps({"type": "token", "content": response.text})
                yield f"data: {payload}\n\n"
                await asyncio.sleep(0)

        done_payload = json.dumps({
            "type": "done",
            "context_sources": 1 if context else 0,
        })
        yield f"data: {done_payload}\n\n"

    except Exception as e:
        error_payload = json.dumps({"type": "error", "message": str(e)})
        yield f"data: {error_payload}\n\n"
