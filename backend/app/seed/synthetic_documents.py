from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClinicalDocument, ClinicalFact, Patient


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


DOCUMENTS = {
    "P001": [
        {
            "document_type": "ADMISSION_NOTE",
            "title": "Synthetic admission note",
            "source_document": "synthetic_admission_note_p001_20260621.txt",
            "authored_at": "2026-06-21T09:00:00",
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
                    "observed_at": "2026-06-21T09:00:00",
                }
            ],
        },
        {
            "document_type": "MEDICATION_RECONCILIATION",
            "title": "Synthetic medication reconciliation",
            "source_document": "synthetic_medication_reconciliation_p001_20260621.txt",
            "authored_at": "2026-06-21T10:00:00",
            "facts": [
                {
                    "fact_type": "ALLERGY_STATEMENT",
                    "subject": "penicillin",
                    "polarity": "NEGATED",
                    "value": "No known allergy to penicillin",
                    "status": "DENIED",
                    "source_section": "Medication Reconciliation",
                    "source_line": 7,
                    "source_start_char": 1,
                    "source_end_char": 31,
                    "observed_at": "2026-06-21T10:00:00",
                }
            ],
        },
    ],
    "P002": [
        {
            "document_type": "ADMISSION_NOTE",
            "title": "Synthetic admission note",
            "source_document": "synthetic_admission_note_p002_20260621.txt",
            "authored_at": "2026-06-21T09:15:00",
            "facts": [
                {
                    "fact_type": "ALLERGY_STATEMENT",
                    "subject": "drug_allergies",
                    "polarity": "NEGATED",
                    "value": "No known drug allergies",
                    "status": "DENIED",
                    "source_section": "Allergies",
                    "source_line": 4,
                    "source_start_char": 1,
                    "source_end_char": 24,
                    "observed_at": "2026-06-21T09:15:00",
                }
            ],
        },
        {
            "document_type": "MEDICATION_RECONCILIATION",
            "title": "Synthetic medication reconciliation",
            "source_document": "synthetic_medication_reconciliation_p002_20260621.txt",
            "authored_at": "2026-06-21T10:15:00",
            "facts": [
                {
                    "fact_type": "ALLERGY_STATEMENT",
                    "subject": "drug_allergies",
                    "polarity": "NEGATED",
                    "value": "No known drug allergies",
                    "status": "DENIED",
                    "source_section": "Medication Reconciliation",
                    "source_line": 5,
                    "source_start_char": 1,
                    "source_end_char": 24,
                    "observed_at": "2026-06-21T10:15:00",
                }
            ],
        },
    ],
    "P003": [
        {
            "document_type": "ADMISSION_NOTE",
            "title": "Synthetic admission note",
            "source_document": "synthetic_admission_note_p003_20260621.txt",
            "authored_at": "2026-06-21T09:30:00",
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
                    "observed_at": "2026-06-21T09:30:00",
                }
            ],
        }
    ],
}


def seed_synthetic_documents(db: Session) -> dict[str, int]:
    documents_created = 0
    facts_created = 0
    duplicates_skipped = 0

    for patient_code, documents in DOCUMENTS.items():
        patient = db.execute(select(Patient).where(Patient.patient_code == patient_code)).scalar_one_or_none()
        if patient is None:
            duplicates_skipped += len(documents)
            continue

        for item in documents:
            document = db.execute(
                select(ClinicalDocument).where(
                    ClinicalDocument.patient_id == patient.id,
                    ClinicalDocument.source_document == item["source_document"],
                )
            ).scalar_one_or_none()
            if document is None:
                document = ClinicalDocument(
                    patient_id=patient.id,
                    document_type=item["document_type"],
                    title=item["title"],
                    source_document=item["source_document"],
                    authored_at=_dt(item["authored_at"]),
                    is_synthetic=True,
                )
                db.add(document)
                db.flush()
                documents_created += 1
            else:
                duplicates_skipped += 1

            for fact in item["facts"]:
                exists = db.execute(
                    select(ClinicalFact).where(
                        ClinicalFact.document_id == document.id,
                        ClinicalFact.fact_type == fact["fact_type"],
                        ClinicalFact.subject == fact["subject"],
                        ClinicalFact.polarity == fact["polarity"],
                        ClinicalFact.source_line == fact["source_line"],
                        ClinicalFact.source_start_char == fact["source_start_char"],
                        ClinicalFact.source_end_char == fact["source_end_char"],
                    )
                ).scalar_one_or_none()
                if exists:
                    duplicates_skipped += 1
                    continue
                db.add(
                    ClinicalFact(
                        patient_id=patient.id,
                        document_id=document.id,
                        fact_type=fact["fact_type"],
                        subject=fact["subject"],
                        polarity=fact["polarity"],
                        value=fact["value"],
                        status=fact["status"],
                        source_section=fact["source_section"],
                        source_line=fact["source_line"],
                        source_start_char=fact["source_start_char"],
                        source_end_char=fact["source_end_char"],
                        observed_at=_dt(fact["observed_at"]),
                    )
                )
                facts_created += 1

    db.commit()
    return {
        "clinical_documents_created": documents_created,
        "clinical_facts_created": facts_created,
        "document_duplicates_skipped": duplicates_skipped,
    }
