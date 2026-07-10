"""
Centralised application settings.

Everything that varies between local development and Render production
lives here, sourced from environment variables. Nothing below should
ever be hard-coded elsewhere in the app — if a new config value is
needed, add it here first.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS_ORIGINS is stored as a comma-separated string in the
        environment (Render's dashboard doesn't handle list-typed env
        vars gracefully), so split it here for actual use."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached so the .env file is parsed once, not on every request."""
    return Settings()
