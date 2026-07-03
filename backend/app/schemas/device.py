from datetime import datetime

from pydantic import BaseModel


class DeviceStateResponse(BaseModel):
    connection: str
    adapter_mode: str = "simulated"
    connection_status: str = "CONNECTED"
    hardware_available: bool = False
    fallback_active: bool = False
    state: str
    led: str
    buzzer: str
    derived_from_event_ids: list[int]
    updated_at: datetime
    last_heartbeat_at: datetime | None = None
    last_command: str | None = None
    last_error: str | None = None
    protocol_version: str = "tracecare-device-v1"


class DeviceHealthResponse(BaseModel):
    connection: str
    adapter_mode: str
    connection_status: str
    hardware_available: bool
    fallback_active: bool
    last_heartbeat_at: datetime | None = None
    last_command: str | None = None
    last_error: str | None = None
    protocol_version: str
