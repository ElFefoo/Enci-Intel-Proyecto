"""
Servicio LLM para el Consultor Veterinario IA.

Cuatro modos configurables via .env (GEMINI_MODE):
  mock      → respuesta hardcodeada, sin API, sin costo (default local)
  api_key   → Gemini API Key de Google AI Studio
  groq      → Groq API (GRATIS, sin tarjeta) ← recomendado para desarrollo
  vertex    → Vertex AI GCP (producción)

Groq: https://console.groq.com  |  Gemini: https://aistudio.google.com/app/apikey
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

# Mapeo de valores de species frontend -> texto legible para el prompt
SPECIES_LABELS = {
    "aves": "Aves (avicultura)",
    "porcinos": "Porcinos",
    "rumiantes": "Rumiantes (bovinos, ovinos, caprinos)",
    "peces": "Peces (acuicultura)",
    "caninos": "Caninos",
    "felinos": "Felinos",
    "equinos": "Equinos",
}


def _build_prompt(question: str, species: str | None, category: str | None, context: str) -> str:
    parts = []
    if species and species in SPECIES_LABELS:
        parts.append(f"Especie animal: {SPECIES_LABELS[species]}")
    elif species:
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
    mode = getattr(settings, "gemini_mode", "mock").lower()

    if mode == "groq":
        async for event in _groq_stream(question, species, category, context, history):
            yield event
    elif mode == "api_key":
        async for event in _api_key_stream(question, species, category, context, history):
            yield event
    elif mode == "vertex":
        async for event in _vertex_stream(question, species, category, context, history):
            yield event
    else:
        async for event in _mock_stream(question, species, category):
            yield event


# ---------------------------------------------------------------------------
# MODO 1: Mock
# ---------------------------------------------------------------------------
async def _mock_stream(question: str, species: str | None, category: str | None) -> AsyncGenerator[str, None]:
    especie_txt = f" para {SPECIES_LABELS.get(species or '', species or '')}"\
        if species else ""
    categoria_txt = f" en categoría {category}" if category else ""

    respuesta = (
        f"**[MOCK Consultor Vet IA]** — Respuesta simulada{especie_txt}{categoria_txt}\n\n"
        f"📋 **Consulta recibida:** {question}\n\n"
        "🔬 **Información técnica (simulada):**\n"
        "- Principio activo: Enrofloxacina 10%\n"
        "- Dosis estándar: 5 mg/kg/día vía subcutánea\n"
        "- Duración tratamiento: 3-5 días\n"
        "- Esperar 14 días antes del sacrificio\n\n"
        "⚠️ *Entorno mock — configura GEMINI_MODE=groq para respuestas reales gratuitas.*"
    )
    words = respuesta.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        await asyncio.sleep(0.03)
    yield f"data: {json.dumps({'type': 'done', 'context_sources': 0, 'sources': [], 'session_id': 'mock-session'})}\n\n"


# ---------------------------------------------------------------------------
# MODO 2: Groq (GRATIS, sin tarjeta)
# pip install groq
# API Key: https://console.groq.com
# ---------------------------------------------------------------------------
async def _groq_stream(
    question: str, species: str | None, category: str | None,
    context: str, history: list[dict] | None,
) -> AsyncGenerator[str, None]:
    try:
        from groq import Groq

        api_key = getattr(settings, "groq_api_key", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY no configurada en .env")

        client = Groq(api_key=api_key)
        prompt = _build_prompt(question, species, category, context)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            for msg in history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})

        loop = asyncio.get_event_loop()
        stream = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=getattr(settings, "groq_model", "llama-3.3-70b-versatile"),
                messages=messages,
                stream=True,
                max_tokens=2048,
            ),
        )

        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                await asyncio.sleep(0)

        yield f"data: {json.dumps({'type': 'done', 'context_sources': 1 if context else 0, 'sources': []})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


# ---------------------------------------------------------------------------
# MODO 3: Gemini API Key
# ---------------------------------------------------------------------------
async def _api_key_stream(
    question: str, species: str | None, category: str | None,
    context: str, history: list[dict] | None,
) -> AsyncGenerator[str, None]:
    try:
        import google.generativeai as genai

        api_key = getattr(settings, "gemini_api_key", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada en .env")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=getattr(settings, "gemini_api_model", "gemini-2.0-flash"),
            system_instruction=SYSTEM_PROMPT,
        )

        chat_history = []
        if history:
            for msg in history[-10:]:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=chat_history)
        prompt = _build_prompt(question, species, category, context)

        loop = asyncio.get_event_loop()
        response_iter = await loop.run_in_executor(
            None, lambda: chat.send_message(prompt, stream=True)
        )

        for chunk in response_iter:
            if chunk.text:
                yield f"data: {json.dumps({'type': 'token', 'content': chunk.text})}\n\n"
                await asyncio.sleep(0)

        yield f"data: {json.dumps({'type': 'done', 'context_sources': 1 if context else 0, 'sources': []})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


# ---------------------------------------------------------------------------
# MODO 4: Vertex AI (producción GCP)
# ---------------------------------------------------------------------------
async def _vertex_stream(
    question: str, species: str | None, category: str | None,
    context: str, history: list[dict] | None,
) -> AsyncGenerator[str, None]:
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, Content, Part

        vertexai.init(project=settings.gcp_project_id, location=settings.vertex_ai_location)
        model = GenerativeModel(model_name=settings.vertex_ai_model, system_instruction=SYSTEM_PROMPT)

        chat_history = []
        if history:
            for msg in history[-10:]:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append(Content(role=role, parts=[Part.from_text(msg["content"])]))

        chat = model.start_chat(history=chat_history)
        prompt = _build_prompt(question, species, category, context)
        responses = chat.send_message(prompt, stream=True)

        for response in responses:
            if response.text:
                yield f"data: {json.dumps({'type': 'token', 'content': response.text})}\n\n"
                await asyncio.sleep(0)

        yield f"data: {json.dumps({'type': 'done', 'context_sources': 1 if context else 0, 'sources': []})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
