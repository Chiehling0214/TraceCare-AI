from pydantic import BaseModel


class AnalysisResultItem(BaseModel):
    patient_id: int
    patient_code: str
    result: str
    event_id: int | None
    rule_id: str


class AnalysisRunResponse(BaseModel):
    analysis_run_id: str
    patients_analyzed: int
    events_created: int
    events_skipped_as_duplicates: int
    insufficient_data_count: int
    results: list[AnalysisResultItem]


class ContradictionAnalysisResultItem(BaseModel):
    patient_id: int
    patient_code: str
    result: str
    event_id: int | None
    rule_id: str
    subject: str | None = None


class ContradictionAnalysisRunResponse(BaseModel):
    analysis_run_id: str
    patients_analyzed: int
    events_created: int
    events_skipped_as_duplicates: int
    insufficient_data_count: int
    results: list[ContradictionAnalysisResultItem]
