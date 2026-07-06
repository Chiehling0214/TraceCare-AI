from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ImportPayload(BaseModel):
    source_filename: str = Field(min_length=1, max_length=255)
    content: str


class ImportErrorItem(BaseModel):
    row: int | None = None
    field: str | None = None
    code: str
    message: str


class ImportPreviewRow(BaseModel):
    row: int
    action: Literal["CREATE", "DUPLICATE_SKIP"]
    patient_code: str | None = None
    source_position: str
    data: dict[str, Any]


class ImportPreviewResponse(BaseModel):
    import_kind: Literal["labs", "documents"]
    schema_version: str
    source_filename: str
    valid: bool
    rows_received: int
    rows_valid: int
    duplicates_detected: int
    errors: list[ImportErrorItem]
    preview_rows: list[ImportPreviewRow]


class ImportCommitResponse(ImportPreviewResponse):
    import_id: int | None
    committed: bool
    records_created: int
    duplicates_skipped: int


class ImportErrorsResponse(BaseModel):
    import_id: int
    errors: list[ImportErrorItem]


class DemoActionResponse(BaseModel):
    status: str
    patients_deleted: int = 0
    patients_created: int = 0
    lab_results_created: int = 0
    clinical_documents_created: int = 0
    clinical_facts_created: int = 0
    events_created: int = 0
    events_escalated: int = 0
    duplicates_skipped: int = 0
    created_at: datetime | None = None
