from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventActionOut(BaseModel):
    id: int
    event_id: int
    patient_id: int
    action_type: str
    actor_label: str
    note: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventActionsResponse(BaseModel):
    event_id: int
    items: list[EventActionOut]
    total: int


class DeferEventRequest(BaseModel):
    reason: str = Field(default="Prototype defer requested for later review.", max_length=500)
    defer_until: datetime | None = None
    actor_label: str = Field(default="prototype-reviewer", max_length=120)
