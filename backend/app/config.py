"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # JWT Settings
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # RSA Keys (load from files in production)
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    fingerprint_salt: str = "change-me-in-production"


settings = Settings()