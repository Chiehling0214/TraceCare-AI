from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ClinicalEvent, ClinicalFact, EventEvidence, Patient


@dataclass(frozen=True)
class AllergyContradictionRule:
    rule_id: str = "ALLERGY_CONTRADICTION"
    fact_type: str = "ALLERGY_STATEMENT"


RULE = AllergyContradictionRule()


def _analysis_run_id() -> str:
    return f"prototype-contradiction-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def _matching_duplicate(db: Session, present: ClinicalFact, negated: ClinicalFact) -> ClinicalEvent | None:
    present_event_ids = select(EventEvidence.event_id).where(
        EventEvidence.target_type == "clinical_fact",
        EventEvidence.target_id == present.id,
        EventEvidence.relation_type == "ASSERTED_FACT",
    )
    return (
        db.execute(
            select(ClinicalEvent)
            .join(EventEvidence, ClinicalEvent.id == EventEvidence.event_id)
            .where(
                ClinicalEvent.rule_id == RULE.rule_id,
                ClinicalEvent.patient_id == present.patient_id,
                ClinicalEvent.id.in_(present_event_ids),
                EventEvidence.target_type == "clinical_fact",
                EventEvidence.target_id == negated.id,
                EventEvidence.relation_type == "DENIED_FACT",
            )
        )
        .scalars()
        .first()
    )


def _create_event(db: Session, patient: Patient, present: ClinicalFact, negated: ClinicalFact) -> ClinicalEvent:
    event = ClinicalEvent(
        patient_id=patient.id,
        event_type="CONTRADICTION",
        severity="REVIEW_REQUIRED",
        status="OPEN",
        title="Contradictory allergy statements require review",
        description=(
            "Prototype rule triggered. Human review is required. "
            f"Conflicting synthetic allergy statements were found for {present.subject}: "
            f"one present statement and one denial. Rule ID: {RULE.rule_id}."
        ),
        rule_id=RULE.rule_id,
    )
    db.add(event)
    db.flush()
    db.add_all(
        [
            EventEvidence(
                event_id=event.id,
                target_type="clinical_fact",
                target_id=present.id,
                relation_type="ASSERTED_FACT",
            ),
            EventEvidence(
                event_id=event.id,
                target_type="clinical_fact",
                target_id=negated.id,
                relation_type="DENIED_FACT",
            ),
            EventEvidence(
                event_id=event.id,
                target_type="clinical_fact",
                target_id=present.id,
                relation_type="SUPPORTS",
            ),
            EventEvidence(
                event_id=event.id,
                target_type="clinical_fact",
                target_id=negated.id,
                relation_type="SUPPORTS",
            ),
            EventEvidence(
                event_id=event.id,
                target_type="clinical_document",
                target_id=present.document_id,
                relation_type="SOURCE_DOCUMENT",
            ),
            EventEvidence(
                event_id=event.id,
                target_type="clinical_document",
                target_id=negated.document_id,
                relation_type="SOURCE_DOCUMENT",
            ),
        ]
    )
    db.flush()
    return event


def _analyze_patient(db: Session, patient: Patient) -> dict[str, object]:
    facts = list(
        db.execute(
            select(ClinicalFact)
            .options(selectinload(ClinicalFact.document))
            .where(ClinicalFact.patient_id == patient.id, ClinicalFact.fact_type == RULE.fact_type)
            .order_by(ClinicalFact.observed_at.asc(), ClinicalFact.id.asc())
        )
        .scalars()
        .all()
    )
    if len(facts) < 2:
        return {
            "patient_id": patient.id,
            "patient_code": patient.patient_code,
            "result": "INSUFFICIENT_DATA",
            "event_id": None,
            "rule_id": RULE.rule_id,
            "subject": None,
        }

    subjects = sorted({fact.subject for fact in facts})
    for subject in subjects:
        subject_facts = [fact for fact in facts if fact.subject == subject]
        present = [fact for fact in subject_facts if fact.polarity == "PRESENT"]
        negated = [fact for fact in subject_facts if fact.polarity == "NEGATED"]
        if not present or not negated:
            continue
        present_fact = present[0]
        negated_fact = negated[0]
        duplicate = _matching_duplicate(db, present_fact, negated_fact)
        if duplicate:
            return {
                "patient_id": patient.id,
                "patient_code": patient.patient_code,
                "result": "DUPLICATE_SKIPPED",
                "event_id": duplicate.id,
                "rule_id": RULE.rule_id,
                "subject": subject,
            }
        event = _create_event(db, patient, present_fact, negated_fact)
        return {
            "patient_id": patient.id,
            "patient_code": patient.patient_code,
            "result": "EVENT_CREATED",
            "event_id": event.id,
            "rule_id": RULE.rule_id,
            "subject": subject,
        }

    return {
        "patient_id": patient.id,
        "patient_code": patient.patient_code,
        "result": "NO_TRIGGER",
        "event_id": None,
        "rule_id": RULE.rule_id,
        "subject": None,
    }


def run_contradiction_analysis(db: Session) -> dict[str, object]:
    patients = list(db.execute(select(Patient).order_by(Patient.patient_code.asc())).scalars().all())
    results = [_analyze_patient(db, patient) for patient in patients]
    db.commit()
    return {
        "analysis_run_id": _analysis_run_id(),
        "patients_analyzed": len(patients),
        "events_created": sum(1 for result in results if result["result"] == "EVENT_CREATED"),
        "events_skipped_as_duplicates": sum(1 for result in results if result["result"] == "DUPLICATE_SKIPPED"),
        "insufficient_data_count": sum(1 for result in results if result["result"] == "INSUFFICIENT_DATA"),
        "results": results,
    }
