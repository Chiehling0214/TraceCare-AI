import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import ClinicalDocument, ClinicalFact, ImportBatch, LabResult, Patient
from app.schemas.imports import ImportErrorItem, ImportPreviewResponse, ImportPreviewRow
from app.services.errors import api_error


LAB_SCHEMA_VERSION = "tracecare-labs-csv-v1"
DOCUMENT_SCHEMA_VERSION = "tracecare-documents-json-v1"
SUPPORTED_LAB_UNITS = {"mg/dL"}
REQUIRED_LAB_FIELDS = [
    "patient_code",
    "display_name",
    "test_name",
    "value",
    "unit",
    "reference_min",
    "reference_max",
    "observed_at",
    "source_document",
]
SUPPORTED_FACT_TYPES = {"ALLERGY_STATEMENT"}
SUPPORTED_POLARITIES = {"PRESENT", "NEGATED"}
SUPPORTED_FACT_STATUSES = {"ACTIVE", "DENIED", "UNKNOWN"}


@dataclass(frozen=True)
class ParsedLabRow:
    row: int
    patient_code: str
    display_name: str
    test_name: str
    value: float
    unit: str
    reference_min: float
    reference_max: float
    observed_at: datetime
    source_document: str


@dataclass(frozen=True)
class ParsedFact:
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


@dataclass(frozen=True)
class ParsedDocument:
    row: int
    patient_code: str
    display_name: str
    document_type: str
    title: str
    source_document: str
    authored_at: datetime
    facts: list[ParsedFact]


def preview_labs(db: Session, source_filename: str, content: str) -> dict[str, object]:
    parsed, errors = _parse_lab_csv(source_filename, content)
    rows = _lab_preview_rows(db, parsed) if not errors else []
    return _preview_payload(
        import_kind="labs",
        schema_version=LAB_SCHEMA_VERSION,
        source_filename=source_filename,
        rows_received=len(parsed) if parsed else _csv_row_count(content),
        rows=rows,
        errors=errors,
    )


def commit_labs(db: Session, source_filename: str, content: str) -> dict[str, object]:
    preview = preview_labs(db, source_filename, content)
    if not preview["valid"]:
        return _failed_commit(db, preview)

    parsed, _ = _parse_lab_csv(source_filename, content)
    created = 0
    skipped = 0
    try:
        for item in parsed:
            patient = _get_or_create_patient(db, item.patient_code, item.display_name)
            if _lab_exists(db, patient.id, item.test_name, item.observed_at, item.source_document):
                skipped += 1
                continue
            db.add(
                LabResult(
                    patient_id=patient.id,
                    test_name=item.test_name,
                    value=item.value,
                    unit=item.unit,
                    reference_min=item.reference_min,
                    reference_max=item.reference_max,
                    observed_at=item.observed_at,
                    source_document=item.source_document,
                )
            )
            created += 1
        batch = _record_batch(db, "labs", source_filename, LAB_SCHEMA_VERSION, "COMMITTED", len(parsed), created, skipped, [])
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise api_error(400, "IMPORT_COMMIT_FAILED", "Import failed and no partial data was committed.") from exc

    return {**preview, "import_id": batch.id, "committed": True, "records_created": created, "duplicates_skipped": skipped}


def preview_documents(db: Session, source_filename: str, content: str) -> dict[str, object]:
    parsed, errors = _parse_document_json(source_filename, content)
    rows = _document_preview_rows(db, parsed) if not errors else []
    return _preview_payload(
        import_kind="documents",
        schema_version=DOCUMENT_SCHEMA_VERSION,
        source_filename=source_filename,
        rows_received=len(parsed),
        rows=rows,
        errors=errors,
    )


def commit_documents(db: Session, source_filename: str, content: str) -> dict[str, object]:
    preview = preview_documents(db, source_filename, content)
    if not preview["valid"]:
        return _failed_commit(db, preview)

    parsed, _ = _parse_document_json(source_filename, content)
    created = 0
    skipped = 0
    try:
        for item in parsed:
            patient = _get_or_create_patient(db, item.patient_code, item.display_name)
            document = _document_by_source(db, patient.id, item.source_document)
            if document is None:
                document = ClinicalDocument(
                    patient_id=patient.id,
                    document_type=item.document_type,
                    title=item.title,
                    source_document=item.source_document,
                    authored_at=item.authored_at,
                    is_synthetic=True,
                )
                db.add(document)
                db.flush()
                created += 1
            else:
                skipped += 1

            for fact in item.facts:
                if _fact_exists(db, document.id, fact):
                    skipped += 1
                    continue
                db.add(
                    ClinicalFact(
                        patient_id=patient.id,
                        document_id=document.id,
                        fact_type=fact.fact_type,
                        subject=fact.subject,
                        polarity=fact.polarity,
                        value=fact.value,
                        status=fact.status,
                        source_section=fact.source_section,
                        source_line=fact.source_line,
                        source_start_char=fact.source_start_char,
                        source_end_char=fact.source_end_char,
                        observed_at=fact.observed_at,
                    )
                )
                created += 1
        batch = _record_batch(
            db, "documents", source_filename, DOCUMENT_SCHEMA_VERSION, "COMMITTED", len(parsed), created, skipped, []
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise api_error(400, "IMPORT_COMMIT_FAILED", "Import failed and no partial data was committed.") from exc

    return {**preview, "import_id": batch.id, "committed": True, "records_created": created, "duplicates_skipped": skipped}


def import_errors(db: Session, import_id: int) -> dict[str, object]:
    batch = db.get(ImportBatch, import_id)
    if batch is None:
        raise api_error(404, "IMPORT_NOT_FOUND", f"Import batch {import_id} was not found.")
    return {"import_id": import_id, "errors": json.loads(batch.errors_json)}


def _parse_lab_csv(source_filename: str, content: str) -> tuple[list[ParsedLabRow], list[ImportErrorItem]]:
    errors: list[ImportErrorItem] = []
    rows: list[ParsedLabRow] = []
    if not source_filename.lower().endswith(".csv"):
        return [], [_error(None, "source_filename", "UNSUPPORTED_FILE_TYPE", "Lab import requires a .csv file.")]
    if not content.strip():
        return [], [_error(None, None, "EMPTY_FILE", "Import file is empty.")]

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        return [], [_error(None, None, "EMPTY_FILE", "CSV file has no header row.")]
    missing = [field for field in REQUIRED_LAB_FIELDS if field not in reader.fieldnames]
    if missing:
        return [], [_error(1, field, "MISSING_REQUIRED_FIELD", f"Missing required CSV field: {field}.") for field in missing]

    identities: set[tuple[str, str, datetime, str]] = set()
    for row_number, raw in enumerate(reader, start=2):
        item = _parse_lab_row(row_number, raw)
        errors.extend(item[1])
        if item[0] is None:
            continue
        identity = (item[0].patient_code, item[0].test_name, item[0].observed_at, item[0].source_document)
        if identity in identities:
            errors.append(_error(row_number, None, "DUPLICATE_IN_FILE", "Duplicate lab row in import file."))
        identities.add(identity)
        rows.append(item[0])
    if not rows and not errors:
        errors.append(_error(None, None, "EMPTY_FILE", "CSV file has no data rows."))
    return rows, errors


def _parse_lab_row(row_number: int, raw: dict[str, str]) -> tuple[ParsedLabRow | None, list[ImportErrorItem]]:
    errors: list[ImportErrorItem] = []
    for field in REQUIRED_LAB_FIELDS:
        if not (raw.get(field) or "").strip():
            errors.append(_error(row_number, field, "MISSING_REQUIRED_FIELD", f"{field} is required."))
    if errors:
        return None, errors
    patient_code = raw["patient_code"].strip()
    if not patient_code.startswith("P"):
        errors.append(_error(row_number, "patient_code", "NON_SYNTHETIC_PATIENT_CODE", "Only synthetic P* codes are allowed."))
    test_name = raw["test_name"].strip().lower()
    unit = raw["unit"].strip()
    if test_name != "creatinine":
        errors.append(_error(row_number, "test_name", "UNSUPPORTED_TEST_NAME", "Only creatinine lab rows are supported."))
    if unit not in SUPPORTED_LAB_UNITS:
        errors.append(_error(row_number, "unit", "INVALID_UNIT", "Only mg/dL is supported."))
    value = _float_field(row_number, raw, "value", errors)
    reference_min = _float_field(row_number, raw, "reference_min", errors)
    reference_max = _float_field(row_number, raw, "reference_max", errors)
    observed_at = _datetime_field(row_number, raw["observed_at"], "observed_at", errors)
    if errors:
        return None, errors
    return (
        ParsedLabRow(
            row=row_number,
            patient_code=patient_code,
            display_name=raw["display_name"].strip(),
            test_name=test_name,
            value=value,
            unit=unit,
            reference_min=reference_min,
            reference_max=reference_max,
            observed_at=observed_at,
            source_document=raw["source_document"].strip(),
        ),
        [],
    )


def _parse_document_json(source_filename: str, content: str) -> tuple[list[ParsedDocument], list[ImportErrorItem]]:
    if not source_filename.lower().endswith(".json"):
        return [], [_error(None, "source_filename", "UNSUPPORTED_FILE_TYPE", "Document import requires a .json file.")]
    if not content.strip():
        return [], [_error(None, None, "EMPTY_FILE", "Import file is empty.")]
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return [], [_error(None, None, "INVALID_JSON", "JSON file is not parseable.")]
    if payload.get("schema_version") != DOCUMENT_SCHEMA_VERSION:
        return [], [_error(None, "schema_version", "INVALID_SCHEMA_VERSION", "Unsupported document schema version.")]
    documents = payload.get("documents")
    if not isinstance(documents, list) or not documents:
        return [], [_error(None, "documents", "EMPTY_FILE", "documents must be a non-empty array.")]

    parsed: list[ParsedDocument] = []
    errors: list[ImportErrorItem] = []
    seen_sources: set[tuple[str, str]] = set()
    for index, document in enumerate(documents, start=1):
        item, item_errors = _parse_document_item(index, document)
        errors.extend(item_errors)
        if item is None:
            continue
        identity = (item.patient_code, item.source_document)
        if identity in seen_sources:
            errors.append(_error(index, "source_document", "DUPLICATE_IN_FILE", "Duplicate document in import file."))
        seen_sources.add(identity)
        parsed.append(item)
    return parsed, errors


def _parse_document_item(index: int, item: Any) -> tuple[ParsedDocument | None, list[ImportErrorItem]]:
    errors: list[ImportErrorItem] = []
    if not isinstance(item, dict):
        return None, [_error(index, None, "INVALID_TYPE", "Document item must be an object.")]
    required = ["patient_code", "display_name", "document_type", "title", "source_document", "authored_at", "facts"]
    for field in required:
        if field not in item or item[field] in (None, ""):
            errors.append(_error(index, field, "MISSING_REQUIRED_FIELD", f"{field} is required."))
    if errors:
        return None, errors
    patient_code = str(item["patient_code"]).strip()
    if not patient_code.startswith("P"):
        errors.append(_error(index, "patient_code", "NON_SYNTHETIC_PATIENT_CODE", "Only synthetic P* codes are allowed."))
    authored_at = _datetime_value(index, item["authored_at"], "authored_at", errors)
    facts_raw = item["facts"]
    if not isinstance(facts_raw, list) or not facts_raw:
        errors.append(_error(index, "facts", "MISSING_REQUIRED_FIELD", "facts must be a non-empty array."))
    facts: list[ParsedFact] = []
    if isinstance(facts_raw, list):
        for fact_index, fact_raw in enumerate(facts_raw, start=1):
            fact, fact_errors = _parse_fact(index, fact_index, fact_raw)
            errors.extend(fact_errors)
            if fact is not None:
                facts.append(fact)
    if errors:
        return None, errors
    return (
        ParsedDocument(
            row=index,
            patient_code=patient_code,
            display_name=str(item["display_name"]).strip(),
            document_type=str(item["document_type"]).strip(),
            title=str(item["title"]).strip(),
            source_document=str(item["source_document"]).strip(),
            authored_at=authored_at,
            facts=facts,
        ),
        [],
    )


def _parse_fact(document_index: int, fact_index: int, fact: Any) -> tuple[ParsedFact | None, list[ImportErrorItem]]:
    row = document_index
    errors: list[ImportErrorItem] = []
    if not isinstance(fact, dict):
        return None, [_error(row, "facts", "INVALID_TYPE", f"facts[{fact_index}] must be an object.")]
    required = [
        "fact_type",
        "subject",
        "polarity",
        "value",
        "status",
        "source_section",
        "source_line",
        "source_start_char",
        "source_end_char",
        "observed_at",
    ]
    for field in required:
        if field not in fact or fact[field] in (None, ""):
            errors.append(_error(row, field, "MISSING_REQUIRED_FIELD", f"facts[{fact_index}].{field} is required."))
    fact_type = str(fact.get("fact_type", "")).strip()
    polarity = str(fact.get("polarity", "")).strip()
    status = str(fact.get("status", "")).strip()
    if fact_type not in SUPPORTED_FACT_TYPES:
        errors.append(_error(row, "fact_type", "UNSUPPORTED_FACT_TYPE", "Only ALLERGY_STATEMENT facts are supported."))
    if polarity and polarity not in SUPPORTED_POLARITIES:
        errors.append(_error(row, "polarity", "INVALID_VALUE", "Unsupported fact polarity."))
    if status and status not in SUPPORTED_FACT_STATUSES:
        errors.append(_error(row, "status", "INVALID_VALUE", "Unsupported fact status."))
    source_line = _int_value(row, fact["source_line"], "source_line", errors) if "source_line" in fact else 0
    start = _int_value(row, fact["source_start_char"], "source_start_char", errors) if "source_start_char" in fact else 0
    end = _int_value(row, fact["source_end_char"], "source_end_char", errors) if "source_end_char" in fact else 0
    observed_at = _datetime_value(row, fact["observed_at"], "observed_at", errors) if "observed_at" in fact else datetime(1970, 1, 1, tzinfo=timezone.utc)
    if start is not None and end is not None and end <= start:
        errors.append(_error(row, "source_end_char", "INVALID_SOURCE_POSITION", "source_end_char must be greater than source_start_char."))
    if errors:
        return None, errors
    return (
        ParsedFact(
            fact_type=fact_type,
            subject=str(fact["subject"]).strip(),
            polarity=polarity,
            value=str(fact["value"]).strip(),
            status=status,
            source_section=str(fact["source_section"]).strip(),
            source_line=source_line,
            source_start_char=start,
            source_end_char=end,
            observed_at=observed_at,
        ),
        [],
    )


def _lab_preview_rows(db: Session, rows: list[ParsedLabRow]) -> list[ImportPreviewRow]:
    preview: list[ImportPreviewRow] = []
    for item in rows:
        patient = _patient_by_code(db, item.patient_code)
        duplicate = patient is not None and _lab_exists(db, patient.id, item.test_name, item.observed_at, item.source_document)
        preview.append(
            ImportPreviewRow(
                row=item.row,
                action="DUPLICATE_SKIP" if duplicate else "CREATE",
                patient_code=item.patient_code,
                source_position=f"{item.source_document}:row:{item.row}",
                data={
                    "test_name": item.test_name,
                    "value": item.value,
                    "unit": item.unit,
                    "observed_at": item.observed_at.isoformat(),
                },
            )
        )
    return preview


def _document_preview_rows(db: Session, rows: list[ParsedDocument]) -> list[ImportPreviewRow]:
    preview: list[ImportPreviewRow] = []
    for item in rows:
        patient = _patient_by_code(db, item.patient_code)
        duplicate = patient is not None and _document_by_source(db, patient.id, item.source_document) is not None
        preview.append(
            ImportPreviewRow(
                row=item.row,
                action="DUPLICATE_SKIP" if duplicate else "CREATE",
                patient_code=item.patient_code,
                source_position=f"{item.source_document}:document:{item.row}",
                data={"document_type": item.document_type, "title": item.title, "facts": len(item.facts)},
            )
        )
    return preview


def _preview_payload(
    *,
    import_kind: str,
    schema_version: str,
    source_filename: str,
    rows_received: int,
    rows: list[ImportPreviewRow],
    errors: list[ImportErrorItem],
) -> dict[str, object]:
    duplicates = sum(1 for row in rows if row.action == "DUPLICATE_SKIP")
    return ImportPreviewResponse(
        import_kind=import_kind,
        schema_version=schema_version,
        source_filename=source_filename,
        valid=not errors,
        rows_received=rows_received,
        rows_valid=len(rows),
        duplicates_detected=duplicates,
        errors=errors,
        preview_rows=rows,
    ).model_dump()


def _failed_commit(db: Session, preview: dict[str, object]) -> dict[str, object]:
    errors = preview["errors"]
    batch = _record_batch(
        db,
        str(preview["import_kind"]),
        str(preview["source_filename"]),
        str(preview["schema_version"]),
        "FAILED",
        int(preview["rows_received"]),
        0,
        0,
        [item.model_dump() if hasattr(item, "model_dump") else item for item in errors],
    )
    db.commit()
    return {**preview, "import_id": batch.id, "committed": False, "records_created": 0, "duplicates_skipped": 0}


def _record_batch(
    db: Session,
    import_kind: str,
    source_filename: str,
    schema_version: str,
    status: str,
    rows_received: int,
    records_created: int,
    duplicates_skipped: int,
    errors: list[dict[str, object]],
) -> ImportBatch:
    batch = ImportBatch(
        import_kind=import_kind,
        source_filename=source_filename,
        schema_version=schema_version,
        status=status,
        rows_received=rows_received,
        records_created=records_created,
        duplicates_skipped=duplicates_skipped,
        errors_json=json.dumps(errors),
        created_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    db.flush()
    return batch


def _get_or_create_patient(db: Session, patient_code: str, display_name: str) -> Patient:
    patient = _patient_by_code(db, patient_code)
    if patient is not None:
        return patient
    patient = Patient(patient_code=patient_code, display_name=display_name)
    db.add(patient)
    db.flush()
    return patient


def _patient_by_code(db: Session, patient_code: str) -> Patient | None:
    return db.execute(select(Patient).where(Patient.patient_code == patient_code)).scalar_one_or_none()


def _lab_exists(db: Session, patient_id: int, test_name: str, observed_at: datetime, source_document: str) -> bool:
    return (
        db.execute(
            select(LabResult).where(
                LabResult.patient_id == patient_id,
                LabResult.test_name == test_name,
                LabResult.observed_at == observed_at,
                LabResult.source_document == source_document,
            )
        ).scalar_one_or_none()
        is not None
    )


def _document_by_source(db: Session, patient_id: int, source_document: str) -> ClinicalDocument | None:
    return db.execute(
        select(ClinicalDocument).where(
            ClinicalDocument.patient_id == patient_id,
            ClinicalDocument.source_document == source_document,
        )
    ).scalar_one_or_none()


def _fact_exists(db: Session, document_id: int, fact: ParsedFact) -> bool:
    return (
        db.execute(
            select(ClinicalFact).where(
                ClinicalFact.document_id == document_id,
                ClinicalFact.fact_type == fact.fact_type,
                ClinicalFact.subject == fact.subject,
                ClinicalFact.polarity == fact.polarity,
                ClinicalFact.source_line == fact.source_line,
                ClinicalFact.source_start_char == fact.source_start_char,
                ClinicalFact.source_end_char == fact.source_end_char,
            )
        ).scalar_one_or_none()
        is not None
    )


def _float_field(row: int, raw: dict[str, str], field: str, errors: list[ImportErrorItem]) -> float:
    try:
        return float(raw[field])
    except ValueError:
        errors.append(_error(row, field, "INVALID_NUMBER", f"{field} must be numeric."))
        return 0.0


def _datetime_field(row: int, value: str, field: str, errors: list[ImportErrorItem]) -> datetime:
    return _datetime_value(row, value, field, errors)


def _datetime_value(row: int, value: Any, field: str, errors: list[ImportErrorItem]) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        errors.append(_error(row, field, "INVALID_TIME_FORMAT", f"{field} must be ISO-8601 datetime."))
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _int_value(row: int, value: Any, field: str, errors: list[ImportErrorItem]) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        errors.append(_error(row, field, "INVALID_INTEGER", f"{field} must be an integer."))
        return 0


def _csv_row_count(content: str) -> int:
    if not content.strip():
        return 0
    rows = list(csv.reader(io.StringIO(content)))
    return max(0, len(rows) - 1)


def _error(row: int | None, field: str | None, code: str, message: str) -> ImportErrorItem:
    return ImportErrorItem(row=row, field=field, code=code, message=message)
