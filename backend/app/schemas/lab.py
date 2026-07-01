from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LabResultOut(BaseModel):
    id: int
    test_name: str
    value: float
    unit: str
    reference_min: float
    reference_max: float
    observed_at: datetime
    source_document: str

    model_config = ConfigDict(from_attributes=True)


class LabListResponse(BaseModel):
    patient_id: int
    items: list[LabResultOut]
    total: int
