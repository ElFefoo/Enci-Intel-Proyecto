from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- GCP / Firebase ---
    gcp_project_id: str = "enci-intel-dev"
    gcp_region: str = "us-central1"
    firestore_database: str = "(default)"
    firebase_project_id: str = "enci-intel-dev"

    # --- Vertex AI ---
    vertex_ai_location: str = "us-central1"
    vertex_ai_model: str = "gemini-1.5-pro"

    # --- Gemini API Key ---
    gemini_api_key: str = ""
    gemini_api_model: str = "gemini-2.0-flash"

    # --- Groq (GRATIS, recomendado para desarrollo) ---
    # API Key en: https://console.groq.com
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # --- Modo LLM ---
    # mock | groq | api_key | vertex
    gemini_mode: str = "mock"

    # --- Rate limiting chat ---
    chat_rate_limit_per_day: int = 50

    # --- Cloud Tasks ---
    cloud_tasks_queue: str = "enci-intel-agents"
    cloud_tasks_handler_url: str = "http://localhost:8000/internal/agents/run"

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"
    disable_auth: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
