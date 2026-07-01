from datetime import datetime

from pydantic import BaseModel


class DeviceStateResponse(BaseModel):
    connection: str
    state: str
    led: str
    buzzer: str
    derived_from_event_ids: list[int]
    updated_at: datetime
