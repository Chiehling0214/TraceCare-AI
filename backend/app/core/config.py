import os
from functools import lru_cache


class Settings:
    app_name = "tracecare-ai-backend"
    version = "0.1.0"
    database_url: str
    frontend_origin: str
    seed_on_startup: bool

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./tracecare.db")
        self.frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
        self.seed_on_startup = os.getenv("SEED_ON_STARTUP", "false").lower() == "true"


@lru_cache
def get_settings() -> Settings:
    return Settings()
