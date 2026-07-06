import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClinicalDocument, ClinicalFact, ImportBatch, LabResult, Patient


VALID_LABS = """patient_code,display_name,test_name,value,unit,reference_min,reference_max,observed_at,source_document
P020,Synthetic Import Patient 20,creatinine,0.8,mg/dL,0.6,1.2,2026-06-24T08:00:00Z,import_labs_20260624.csv
P020,Synthetic Import Patient 20,creatinine,1.4,mg/dL,0.6,1.2,2026-06-25T08:00:00Z,import_labs_20260625.csv
P021,Synthetic Import Patient 21,creatinine,0.9,mg/dL,0.6,1.2,2026-06-24T08:00:00Z,import_labs_20260624.csv
"""


def _payload(source_filename: str, content: str) -> dict[str, str]:
    return {"source_filename": source_filename, "content": content}


def _valid_documents(patient_code: str = "P020") -> dict:
    return {
        "schema_version": "tracecare-documents-json-v1",
        "documents": [
            {
                "patient_code": patient_code,
                "display_name": "Synthetic Import Patient 20",
                "document_type": "ADMISSION_NOTE",
                "title": "Synthetic import admission note",
                "source_document": f"import_note_{patient_code.lower()}_20260625.txt",
                "authored_at": "2026-06-25T09:00:00Z",
                "facts": [
                    {
                        "fact_type": "ALLERGY_STATEMENT",
                        "subject": "penicillin",
                        "polarity": "PRESENT",
                        "value": "Allergy: Penicillin",
                        "status": "ACTIVE",
                        "source_section": "Allergies",
                        "source_line": 4,
                        "source_start_char": 10,
                        "source_end_char": 20,
                        "observed_at": "2026-06-25T09:00:00Z",
                    }
                ],
            }
        ],
    }


def test_valid_lab_preview_and_commit_preserves_source_metadata(seeded_client, db_session: Session):
    preview = seeded_client.post("/api/import/labs/preview", json=_payload("valid_labs.csv", VALID_LABS))

    assert preview.status_code == 200
    preview_payload = preview.json()
    assert preview_payload["valid"] is True
    assert preview_payload["rows_valid"] == 3
    assert preview_payload["preview_rows"][0]["source_position"] == "import_labs_20260624.csv:row:2"

    commit = seeded_client.post("/api/import/labs/commit", json=_payload("valid_labs.csv", VALID_LABS))

    assert commit.status_code == 200
    payload = commit.json()
    assert payload["committed"] is True
    assert payload["records_created"] == 3
    patient = db_session.execute(select(Patient).where(Patient.patient_code == "P020")).scalar_one()
    labs = db_session.execute(select(LabResult).where(LabResult.patient_id == patient.id)).scalars().all()
    assert {lab.source_document for lab in labs} == {"import_labs_20260624.csv", "import_labs_20260625.csv"}
    assert db_session.get(ImportBatch, payload["import_id"]).status == "COMMITTED"


def test_missing_required_lab_field_reports_error(seeded_client):
    content = "patient_code,display_name,test_name,value,unit,reference_min,reference_max,observed_at\nP020,Synthetic,creatinine,0.8,mg/dL,0.6,1.2,2026-06-24T08:00:00Z\n"

    response = seeded_client.post("/api/import/labs/preview", json=_payload("missing.csv", content))

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert any(error["code"] == "MISSING_REQUIRED_FIELD" and error["field"] == "source_document" for error in payload["errors"])


def test_invalid_lab_type_time_unit_and_empty_file(seeded_client):
    invalid = """patient_code,display_name,test_name,value,unit,reference_min,reference_max,observed_at,source_document
P020,Synthetic,creatinine,not-a-number,umol/L,0.6,1.2,not-a-time,invalid.csv
"""

    response = seeded_client.post("/api/import/labs/preview", json=_payload("invalid.csv", invalid)).json()
    assert {error["code"] for error in response["errors"]} >= {"INVALID_NUMBER", "INVALID_UNIT", "INVALID_TIME_FORMAT"}

    empty = seeded_client.post("/api/import/labs/preview", json=_payload("empty.csv", "")).json()
    assert empty["errors"][0]["code"] == "EMPTY_FILE"


def test_unsupported_file_format_is_rejected(seeded_client):
    response = seeded_client.post("/api/import/labs/preview", json=_payload("labs.txt", VALID_LABS)).json()

    assert response["valid"] is False
    assert response["errors"][0]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_duplicate_lab_import_is_explicitly_skipped(seeded_client):
    first = seeded_client.post("/api/import/labs/commit", json=_payload("valid_labs.csv", VALID_LABS)).json()
    second = seeded_client.post("/api/import/labs/commit", json=_payload("valid_labs.csv", VALID_LABS)).json()

    assert first["records_created"] == 3
    assert second["records_created"] == 0
    assert second["duplicates_skipped"] == 3
    assert second["duplicates_detected"] == 3


def test_duplicate_rows_inside_file_are_invalid(seeded_client):
    duplicate = VALID_LABS + "P020,Synthetic Import Patient 20,creatinine,1.4,mg/dL,0.6,1.2,2026-06-25T08:00:00Z,import_labs_20260625.csv\n"

    response = seeded_client.post("/api/import/labs/preview", json=_payload("duplicate.csv", duplicate)).json()

    assert response["valid"] is False
    assert any(error["code"] == "DUPLICATE_IN_FILE" for error in response["errors"])


def test_valid_document_import_and_patient_isolation(seeded_client, db_session: Session):
    seeded_client.post("/api/import/labs/commit", json=_payload("valid_labs.csv", VALID_LABS))
    content = json.dumps(_valid_documents("P021"))

    response = seeded_client.post("/api/import/documents/commit", json=_payload("documents.json", content))

    assert response.status_code == 200
    payload = response.json()
    assert payload["committed"] is True
    patient = db_session.execute(select(Patient).where(Patient.patient_code == "P021")).scalar_one()
    documents = db_session.execute(select(ClinicalDocument).where(ClinicalDocument.patient_id == patient.id)).scalars().all()
    facts = db_session.execute(select(ClinicalFact).where(ClinicalFact.patient_id == patient.id)).scalars().all()
    assert len(documents) == 1
    assert len(facts) == 1
    assert facts[0].source_line == 4
    assert facts[0].source_start_char == 10


def test_invalid_document_missing_source_position_and_unsupported_fact_type_rolls_back(seeded_client, db_session: Session):
    data = _valid_documents("P022")
    data["documents"][0]["facts"][0].pop("source_start_char")
    data["documents"][0]["facts"][0]["fact_type"] = "UNSUPPORTED"

    response = seeded_client.post("/api/import/documents/commit", json=_payload("bad_documents.json", json.dumps(data)))

    assert response.status_code == 200
    payload = response.json()
    assert payload["committed"] is False
    assert {error["code"] for error in payload["errors"]} >= {"MISSING_REQUIRED_FIELD", "UNSUPPORTED_FACT_TYPE"}
    assert db_session.execute(select(Patient).where(Patient.patient_code == "P022")).scalar_one_or_none() is None
    errors = seeded_client.get(f"/api/imports/{payload['import_id']}/errors").json()
    assert errors["errors"]


def test_non_synthetic_patient_code_is_rejected(seeded_client):
    data = VALID_LABS.replace("P020", "REAL001", 1)

    response = seeded_client.post("/api/import/labs/preview", json=_payload("real.csv", data)).json()

    assert any(error["code"] == "NON_SYNTHETIC_PATIENT_CODE" for error in response["errors"])


def test_reset_seed_and_run_demo_are_repeatable(seeded_client):
    first_reset = seeded_client.post("/api/development/reset-demo").json()
    second_reset = seeded_client.post("/api/development/reset-demo").json()
    first_seed = seeded_client.post("/api/development/seed-demo").json()
    second_seed = seeded_client.post("/api/development/seed-demo").json()
    first_run = seeded_client.post("/api/development/run-demo-analysis").json()
    second_run = seeded_client.post("/api/development/run-demo-analysis").json()

    assert first_reset["status"] == "RESET"
    assert second_reset["patients_deleted"] == 0
    assert first_seed["patients_created"] >= 3
    assert second_seed["patients_created"] == 0
    assert second_seed["duplicates_skipped"] > 0
    assert first_run["status"] == "ANALYZED"
    assert second_run["status"] == "ANALYZED"
    assert second_run["duplicates_skipped"] >= first_run["duplicates_skipped"]


def test_import_failure_does_not_create_partial_lab_data(seeded_client, db_session: Session):
    invalid = VALID_LABS + "P023,Synthetic Bad,creatinine,broken,mg/dL,0.6,1.2,2026-06-26T08:00:00Z,bad.csv\n"

    response = seeded_client.post("/api/import/labs/commit", json=_payload("bad.csv", invalid)).json()

    assert response["committed"] is False
    assert db_session.execute(select(Patient).where(Patient.patient_code == "P023")).scalar_one_or_none() is None
