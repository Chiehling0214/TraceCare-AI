from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClinicalEvent, EvidenceLink, LabResult, Patient


@dataclass(frozen=True)
class RapidIncreaseRule:
    rule_id: str = "RAPID_INCREASE"
    test_name: str = "creatinine"
    previous_value: float = 0.8
    current_value: float = 1.3
    max_hours: float = 24.0
    unit: str = "mg/dL"


RULE = RapidIncreaseRule()


def _analysis_run_id() -> str:
    return f"prototype-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def _matching_duplicate(db: Session, previous: LabResult, current: LabResult) -> ClinicalEvent | None:
    previous_event_ids = select(EvidenceLink.event_id).where(
        EvidenceLink.lab_result_id == previous.id,
        EvidenceLink.relation_type == "PREVIOUS_VALUE",
    )
    return (
        db.execute(
            select(ClinicalEvent)
            .join(EvidenceLink, ClinicalEvent.id == EvidenceLink.event_id)
            .where(
                ClinicalEvent.rule_id == RULE.rule_id,
                ClinicalEvent.patient_id == previous.patient_id,
                ClinicalEvent.id.in_(previous_event_ids),
                EvidenceLink.lab_result_id == current.id,
                EvidenceLink.relation_type == "CURRENT_VALUE",
            )
        )
        .scalars()
        .first()
    )


def _create_event(db: Session, patient: Patient, previous: LabResult, current: LabResult, hours: float) -> ClinicalEvent:
    event = ClinicalEvent(
        patient_id=patient.id,
        event_type="RAPID_LAB_CHANGE",
        severity="REVIEW_REQUIRED",
        status="OPEN",
        title="Creatinine rapid increase requires review",
        description=(
            "Prototype rule triggered. Human review is required. "
            f"Creatinine changed from {previous.value:g} {previous.unit} to {current.value:g} {current.unit}; "
            f"time difference {hours:g} hours; Rule ID: {RULE.rule_id}."
        ),
        rule_id=RULE.rule_id,
    )
    db.add(event)
    db.flush()
    db.add_all(
        [
            EvidenceLink(event_id=event.id, lab_result_id=previous.id, relation_type="PREVIOUS_VALUE"),
            EvidenceLink(event_id=event.id, lab_result_id=current.id, relation_type="CURRENT_VALUE"),
            EvidenceLink(event_id=event.id, lab_result_id=previous.id, relation_type="SUPPORTS"),
            EvidenceLink(event_id=event.id, lab_result_id=current.id, relation_type="SUPPORTS"),
        ]
    )
    db.flush()
    return event


def _analyze_patient(db: Session, patient: Patient) -> dict[str, object]:
    labs = list(
        db.execute(
            select(LabResult)
            .where(LabResult.patient_id == patient.id, LabResult.test_name == RULE.test_name)
            .order_by(LabResult.observed_at.asc())
        )
        .scalars()
        .all()
    )
    if len(labs) < 2:
        return {
            "patient_id": patient.id,
            "patient_code": patient.patient_code,
            "result": "INSUFFICIENT_DATA",
            "event_id": None,
            "rule_id": RULE.rule_id,
        }

    for previous, current in zip(labs, labs[1:]):
        hours = (current.observed_at - previous.observed_at).total_seconds() / 3600
        triggers = (
            previous.value == RULE.previous_value
            and current.value == RULE.current_value
            and previous.unit == RULE.unit
            and current.unit == RULE.unit
            and 0 <= hours <= RULE.max_hours
        )
        if not triggers:
            continue
        duplicate = _matching_duplicate(db, previous, current)
        if duplicate:
            return {
                "patient_id": patient.id,
                "patient_code": patient.patient_code,
                "result": "DUPLICATE_SKIPPED",
                "event_id": duplicate.id,
                "rule_id": RULE.rule_id,
            }
        event = _create_event(db, patient, previous, current, hours)
        return {
            "patient_id": patient.id,
            "patient_code": patient.patient_code,
            "result": "EVENT_CREATED",
            "event_id": event.id,
            "rule_id": RULE.rule_id,
        }

    return {
        "patient_id": patient.id,
        "patient_code": patient.patient_code,
        "result": "NO_TRIGGER",
        "event_id": None,
        "rule_id": RULE.rule_id,
    }


def run_analysis(db: Session) -> dict[str, object]:
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
