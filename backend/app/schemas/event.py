from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.patient import PatientBase


class EventOut(BaseModel):
    id: int
    event_type: str
    severity: str
    status: str
    title: str
    description: str
    rule_id: str
    created_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    patient_id: int
    items: list[EventOut]
    total: int


class EventActionResponse(BaseModel):
    id: int
    status: str
    acknowledged_at: datetime | None
    resolved_at: datetime | None


class EventAnalysis(BaseModel):
    test_name: str
    previous_value: float
    current_value: float
    unit: str
    previous_observed_at: datetime
    current_observed_at: datetime
    time_difference_hours: float


class EvidenceLabResult(BaseModel):
    id: int
    test_name: str
    value: float
    unit: str
    observed_at: datetime
    source_document: str


class EvidenceLinkOut(BaseModel):
    evidence_link_id: int
    relation_type: str
    lab_result: EvidenceLabResult


class EvidenceDocument(BaseModel):
    id: int
    document_type: str
    title: str
    source_document: str
    authored_at: datetime
    is_synthetic: bool


class EvidenceFact(BaseModel):
    id: int
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
    document: EvidenceDocument


class TypedEvidenceOut(BaseModel):
    event_evidence_id: int
    target_type: str
    target_id: int
    relation_type: str
    clinical_fact: EvidenceFact | None = None
    clinical_document: EvidenceDocument | None = None


class EventDetail(EventOut):
    patient: PatientBase
    analysis: EventAnalysis | None
    evidence: list[EvidenceLinkOut]
    document_evidence: list[TypedEvidenceOut] = Field(default_factory=list)
