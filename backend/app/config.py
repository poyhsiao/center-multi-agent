"""Application configuration."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Accept both uppercase and lowercase
    )

    # JWT Settings
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # RSA Keys (load from files in production)
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"

    # Database
    database_url: Optional[str] = None

    @property
    def database_url_with_fallback(self) -> str:
        """Get database URL with fallback for Docker."""
        if self.database_url:
            return self.database_url
        return "postgresql+asyncpg://postgres:postgres@localhost:5433/center_multi_agent"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    fingerprint_salt: str = "change-me-in-production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()