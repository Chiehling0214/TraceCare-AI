from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClinicalDocumentOut(BaseModel):
    id: int
    patient_id: int
    document_type: str
    title: str
    source_document: str
    authored_at: datetime
    created_at: datetime
    is_synthetic: bool

    model_config = ConfigDict(from_attributes=True)


class ClinicalDocumentListResponse(BaseModel):
    patient_id: int
    items: list[ClinicalDocumentOut]
    total: int
