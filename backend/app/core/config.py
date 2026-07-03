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
    device_adapter_mode: str
    device_serial_port: str
    device_serial_baud_rate: int
    device_serial_timeout_seconds: float
    device_heartbeat_timeout_seconds: float

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./tracecare.db")
        self.frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
        self.seed_on_startup = os.getenv("SEED_ON_STARTUP", "false").lower() == "true"
        self.llm_mode = os.getenv("LLM_MODE", "disabled").lower()
        self.local_llm_base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434")
        self.local_llm_model = os.getenv("LOCAL_LLM_MODEL", "")
        self.local_llm_timeout_seconds = int(os.getenv("LOCAL_LLM_TIMEOUT_SECONDS", "120"))
        self.device_adapter_mode = os.getenv("DEVICE_ADAPTER_MODE", "simulated").lower()
        self.device_serial_port = os.getenv("DEVICE_SERIAL_PORT", "")
        self.device_serial_baud_rate = int(os.getenv("DEVICE_SERIAL_BAUD_RATE", "115200"))
        self.device_serial_timeout_seconds = float(os.getenv("DEVICE_SERIAL_TIMEOUT_SECONDS", "1.0"))
        self.device_heartbeat_timeout_seconds = float(os.getenv("DEVICE_HEARTBEAT_TIMEOUT_SECONDS", "3.0"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
