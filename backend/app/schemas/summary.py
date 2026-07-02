from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SummaryRequest(BaseModel):
    prefer_llm: bool = True


class EvidenceItemOut(BaseModel):
    id: str
    type: str
    label: str
    text: str
    numeric_values: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidencePackageOut(BaseModel):
    package_id: str
    patient_id: int
    patient_code: str
    summary_kind: str
    evidence_items: list[EvidenceItemOut]
    sufficient: bool
    insufficiency_reason: str | None = None


class SummarySentenceOut(BaseModel):
    index: int
    text: str
    evidence_ids: list[str]


class SummaryResponse(BaseModel):
    id: str
    patient_id: int
    patient_code: str
    summary_kind: str
    status: str
    validation_status: str
    adapter_mode: str
    model_name: str | None = None
    local_only: bool
    text: str
    sentences: list[SummarySentenceOut]
    evidence_package: EvidencePackageOut
    validation_errors: list[str] = Field(default_factory=list)
    abstention_reason: str | None = None
    created_at: datetime


class SummaryEvidenceResponse(BaseModel):
    summary_id: str
    evidence_package: EvidencePackageOut
