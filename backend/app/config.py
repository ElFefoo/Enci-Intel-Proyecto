from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    DEBUG: bool = False

    # GCP
    GCP_PROJECT_ID: str = "enci-intel-dev"
    GCP_REGION: str = "us-central1"

    # Keycloak
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "enci-intel"
    KEYCLOAK_AUDIENCE: str = "enci-intel-backend"

    # Cloud Tasks
    CLOUD_TASKS_QUEUE: str = "enci-intel-agents"
    INTERNAL_API_SECRET: str = "change-me"

    @property
    def KEYCLOAK_JWKS_URL(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/certs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
