# Backend settings via pydantic-settings

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "Restaurant Allergen Advisor"
    debug: bool = False
    cors_origins: list[str] = ["*"]

    # Database
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "restaurant"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    database_url: Optional[str] = None

    model_config = {"env_file": ".env"}

settings = Settings()
