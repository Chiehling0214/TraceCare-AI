from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    id: int
    patient_code: str
    display_name: str
    is_synthetic: bool = True

    model_config = ConfigDict(from_attributes=True)


class PatientSummary(PatientBase):
    current_severity: str
    open_event_count: int
    latest_lab_observed_at: datetime | None
    risk_reasons: list[str] = Field(default_factory=list)
    oldest_unresolved_event_at: datetime | None = None
    driver_event_ids: list[int] = Field(default_factory=list)


class PatientDetail(PatientSummary):
    created_at: datetime


class PatientListResponse(BaseModel):
    items: list[PatientSummary]
    total: int
