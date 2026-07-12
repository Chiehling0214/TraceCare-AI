from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import (
    ClinicalDocument,
    ClinicalEvent,
    ClinicalFact,
    EventAction,
    EventEvidence,
    EvidenceLink,
    ImportBatch,
    LabResult,
    Patient,
    SummaryRecord,
)
from app.seed.synthetic import seed_synthetic_data
from app.services.contradiction_service import run_contradiction_analysis
from app.services.import_service import commit_documents, commit_labs
from app.services.risk_service import run_risk_evaluation
from app.services.rule_service import run_analysis


DEMO_DATA_DIR = Path(__file__).resolve().parents[1] / "seed"


def reset_demo(db: Session) -> dict[str, object]:
    patients_deleted = db.query(Patient).count()
    for model in [
        SummaryRecord,
        EventAction,
        EventEvidence,
        EvidenceLink,
        ClinicalEvent,
        ClinicalFact,
        ClinicalDocument,
        LabResult,
        Patient,
        ImportBatch,
    ]:
        db.query(model).delete()
    db.commit()
    return {"status": "RESET", "patients_deleted": patients_deleted, "created_at": datetime.now(timezone.utc)}


def seed_demo(db: Session) -> dict[str, object]:
    result = seed_synthetic_data(db)
    labs_content = (DEMO_DATA_DIR / "demo_labs.csv").read_text(encoding="utf-8")
    documents_content = (DEMO_DATA_DIR / "demo_documents.json").read_text(encoding="utf-8")
    labs = commit_labs(db, "demo_labs.csv", labs_content)
    documents = commit_documents(db, "demo_documents.json", documents_content)
    return {
        "status": "SEEDED",
        **result,
        "lab_results_created": int(result.get("lab_results_created", 0)) + int(labs["records_created"]),
        "clinical_documents_created": int(result.get("clinical_documents_created", 0))
        + _created_documents_from_import(documents),
        "clinical_facts_created": int(result.get("clinical_facts_created", 0)) + _created_facts_from_import(documents),
        "duplicates_skipped": int(result.get("duplicates_skipped", 0))
        + int(result.get("document_duplicates_skipped", 0))
        + int(labs["duplicates_skipped"])
        + int(documents["duplicates_skipped"]),
        "created_at": datetime.now(timezone.utc),
    }


def run_demo_analysis(db: Session) -> dict[str, object]:
    lab_result = run_analysis(db)
    contradiction_result = run_contradiction_analysis(db)
    risk_result = run_risk_evaluation(db)
    return {
        "status": "ANALYZED",
        "events_created": int(lab_result["events_created"]) + int(contradiction_result["events_created"]),
        "events_escalated": int(risk_result["events_escalated"]),
        "duplicates_skipped": int(lab_result["events_skipped_as_duplicates"])
        + int(contradiction_result["events_skipped_as_duplicates"]),
        "lab": lab_result,
        "contradiction": contradiction_result,
        "risk": risk_result,
        "created_at": datetime.now(timezone.utc),
    }


def _created_documents_from_import(payload: dict[str, object]) -> int:
    return sum(1 for row in payload["preview_rows"] if row["action"] == "CREATE")


def _created_facts_from_import(payload: dict[str, object]) -> int:
    return int(payload["records_created"]) - _created_documents_from_import(payload)
