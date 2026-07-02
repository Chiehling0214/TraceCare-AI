import os
from functools import lru_cache


class Settings:
    app_name = "tracecare-ai-backend"
    version = "0.1.0"
    database_url: str
    frontend_origin: str
    seed_on_startup: bool
    llm_mode: str
    local_llm_base_url: str
    local_llm_model: str
    local_llm_timeout_seconds: int

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./tracecare.db")
        self.frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
        self.seed_on_startup = os.getenv("SEED_ON_STARTUP", "false").lower() == "true"
        self.llm_mode = os.getenv("LLM_MODE", "disabled").lower()
        self.local_llm_base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434")
        self.local_llm_model = os.getenv("LOCAL_LLM_MODEL", "")
        self.local_llm_timeout_seconds = int(os.getenv("LOCAL_LLM_TIMEOUT_SECONDS", "120"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
