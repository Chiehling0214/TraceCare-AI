from datetime import datetime

from pydantic import BaseModel, Field


class RiskReason(BaseModel):
    code: str
    message: str
    event_ids: list[int] = Field(default_factory=list)


class PatientRiskResponse(BaseModel):
    patient_id: int
    patient_code: str
    risk_state: str
    risk_reasons: list[RiskReason]
    unresolved_event_count: int
    oldest_unresolved_event_at: datetime | None
    driver_event_ids: list[int]


class RiskEvaluationRequest(BaseModel):
    evaluated_at: datetime | None = None


class RiskEvaluationResponse(BaseModel):
    evaluation_run_id: str
    evaluated_at: datetime
    patients_evaluated: int
    events_escalated: int
    results: list[PatientRiskResponse]
