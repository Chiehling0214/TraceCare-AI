from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import ClinicalEvent, LabResult, Patient


SEVERITY_RANK = {"HIGH_RISK": 0, "REVIEW_REQUIRED": 1, "NORMAL": 2}


def patient_summary(db: Session, patient: Patient) -> dict[str, object]:
    unresolved = (
        db.execute(
            select(ClinicalEvent).where(
                ClinicalEvent.patient_id == patient.id,
                ClinicalEvent.status.in_(["OPEN", "ACKNOWLEDGED"]),
            )
        )
        .scalars()
        .all()
    )
    open_events = [event for event in unresolved if event.status == "OPEN"]
    if open_events:
        current_severity = max((event.severity for event in open_events), key=lambda item: -SEVERITY_RANK.get(item, 99))
    elif unresolved:
        current_severity = "REVIEW_REQUIRED"
    else:
        current_severity = "NORMAL"

    latest_lab = db.execute(
        select(func.max(LabResult.observed_at)).where(LabResult.patient_id == patient.id)
    ).scalar_one_or_none()
    return {
        "id": patient.id,
        "patient_code": patient.patient_code,
        "display_name": patient.display_name,
        "is_synthetic": True,
        "current_severity": current_severity,
        "open_event_count": len(unresolved),
        "latest_lab_observed_at": latest_lab,
    }


def ordered_patient_summaries(db: Session) -> list[dict[str, object]]:
    patients = db.execute(select(Patient)).scalars().all()
    summaries = [patient_summary(db, patient) for patient in patients]
    return sorted(
        summaries,
        key=lambda item: (
            SEVERITY_RANK.get(str(item["current_severity"]), 99),
            item["latest_lab_observed_at"] is None,
            -item["latest_lab_observed_at"].timestamp() if item["latest_lab_observed_at"] else 0,
        ),
    )


def get_patient(db: Session, patient_id: int) -> Patient | None:
    return db.get(Patient, patient_id)


def labs_for_patient(db: Session, patient_id: int) -> list[LabResult]:
    statement: Select[tuple[LabResult]] = (
        select(LabResult).where(LabResult.patient_id == patient_id).order_by(LabResult.observed_at.asc())
    )
    return list(db.execute(statement).scalars().all())


def events_for_patient(db: Session, patient_id: int) -> list[ClinicalEvent]:
    return list(
        db.execute(
            select(ClinicalEvent)
            .where(ClinicalEvent.patient_id == patient_id)
            .order_by(ClinicalEvent.created_at.desc(), ClinicalEvent.id.desc())
        )
        .scalars()
        .all()
    )
