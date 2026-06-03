from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gcp_project_id: str = "enci-intel-dev"
    gcp_region: str = "us-central1"
    firestore_database: str = "(default)"

    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "enci-intel"
    keycloak_client_id: str = "enci-intel-backend"
    keycloak_jwks_url: str = "http://localhost:8080/realms/enci-intel/protocol/openid-connect/certs"

    vertex_ai_location: str = "us-central1"
    vertex_ai_model: str = "gemini-1.5-pro"

    cloud_tasks_queue: str = "enci-intel-agents"
    cloud_tasks_handler_url: str = "http://localhost:8000/internal/agents/run"

    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"
    secret_key: str = "changeme"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
