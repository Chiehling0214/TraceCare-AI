from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class PatientDetail(PatientSummary):
    created_at: datetime


class PatientListResponse(BaseModel):
    items: list[PatientSummary]
    total: int
