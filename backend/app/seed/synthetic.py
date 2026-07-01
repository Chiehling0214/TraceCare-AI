from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LabResult, Patient


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


PATIENTS = [
    {"patient_code": "P001", "display_name": "Synthetic Patient A"},
    {"patient_code": "P002", "display_name": "Synthetic Patient B"},
    {"patient_code": "P003", "display_name": "Synthetic Patient C"},
]

LABS = {
    "P001": [
        ("2026-06-20T08:00:00", 0.8, "synthetic_lab_report_20260620.csv"),
        ("2026-06-21T08:00:00", 1.3, "synthetic_lab_report_20260621.csv"),
    ],
    "P002": [
        ("2026-06-20T08:00:00", 0.9, "synthetic_lab_report_20260620.csv"),
        ("2026-06-21T08:00:00", 0.9, "synthetic_lab_report_20260621.csv"),
    ],
    "P003": [
        ("2026-06-21T08:00:00", 1.0, "synthetic_lab_report_20260621.csv"),
    ],
}


def seed_synthetic_data(db: Session) -> dict[str, int]:
    patients_created = 0
    labs_created = 0
    duplicates_skipped = 0

    for item in PATIENTS:
        patient = db.execute(select(Patient).where(Patient.patient_code == item["patient_code"])).scalar_one_or_none()
        if patient is None:
            patient = Patient(**item)
            db.add(patient)
            db.flush()
            patients_created += 1
        else:
            duplicates_skipped += 1

        for observed_at, value, source_document in LABS[item["patient_code"]]:
            exists = db.execute(
                select(LabResult).where(
                    LabResult.patient_id == patient.id,
                    LabResult.test_name == "creatinine",
                    LabResult.observed_at == _dt(observed_at),
                    LabResult.source_document == source_document,
                )
            ).scalar_one_or_none()
            if exists:
                duplicates_skipped += 1
                continue
            db.add(
                LabResult(
                    patient_id=patient.id,
                    test_name="creatinine",
                    value=value,
                    unit="mg/dL",
                    reference_min=0.6,
                    reference_max=1.2,
                    observed_at=_dt(observed_at),
                    source_document=source_document,
                )
            )
            labs_created += 1

    db.commit()
    return {
        "patients_created": patients_created,
        "lab_results_created": labs_created,
        "duplicates_skipped": duplicates_skipped,
    }
