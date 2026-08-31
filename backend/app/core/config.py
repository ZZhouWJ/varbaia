from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Verbaia API"
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"
    owner_bootstrap_token: str = "local-development-only"
    media_import_allowed_hosts: str = "youtube.com,youtu.be,vimeo.com"
    database_url: str = "postgresql+asyncpg://varbaia:change-me@localhost:5432/varbaia"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "local-development-only-change-before-deploy"
    access_token_minutes: int = 15
    refresh_token_days: int = 14
    allow_registration: bool = False

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_media_hosts(self) -> set[str]:
        return {
            host.strip().lower()
            for host in self.media_import_allowed_hosts.split(",")
            if host.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
