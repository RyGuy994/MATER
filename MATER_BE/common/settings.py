# common/settings.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration managed via environment variables (.env supported).
    Provides type safety and default values for runtime configuration.
    """
    SECRET_KEY: str
    APP_SETTINGS: str = "common.base.ProductionConfig"
    DATABASETYPE: str = "postgresql"

    DB_USERNAME: str = "mater_user"
    DB_PASSWORD: str = "mater_pass"
    DB_HOST: str = "localhost"
    DB_NAME: str = "mater"

    class Config:
        env_file = ".env"  # Load from .env if available
        env_file_encoding = "utf-8"


# Singleton instance available everywhere
settings = Settings()
