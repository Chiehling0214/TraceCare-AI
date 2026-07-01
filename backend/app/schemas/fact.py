from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClinicalFactOut(BaseModel):
    id: int
    patient_id: int
    document_id: int
    fact_type: str
    subject: str
    polarity: str
    value: str
    status: str
    source_section: str
    source_line: int
    source_start_char: int
    source_end_char: int
    observed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClinicalFactListResponse(BaseModel):
    patient_id: int
    items: list[ClinicalFactOut]
    total: int
