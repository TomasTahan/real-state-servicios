"""
Configuración del sistema de consulta de deudas de servicios
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Browser-Use Cloud
    BROWSER_USE_CLOUD: bool = True

    # Agent settings
    MAX_FAILURES: int = 3
    STEP_TIMEOUT: int = 30
    MAX_ACTIONS_PER_STEP: int = 5

    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar campos extra del .env


settings = Settings()
