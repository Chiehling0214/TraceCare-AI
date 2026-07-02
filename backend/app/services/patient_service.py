from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import ClinicalEvent, LabResult, Patient
from app.services.risk_service import RISK_RANK, patient_risk


SEVERITY_RANK = RISK_RANK


def patient_summary(db: Session, patient: Patient) -> dict[str, object]:
    risk = patient_risk(db, patient.id)
    latest_lab = db.execute(
        select(func.max(LabResult.observed_at)).where(LabResult.patient_id == patient.id)
    ).scalar_one_or_none()
    return {
        "id": patient.id,
        "patient_code": patient.patient_code,
        "display_name": patient.display_name,
        "is_synthetic": True,
        "current_severity": risk.risk_state,
        "open_event_count": risk.unresolved_event_count,
        "latest_lab_observed_at": latest_lab,
        "risk_reasons": [reason.message for reason in risk.risk_reasons],
        "oldest_unresolved_event_at": risk.oldest_unresolved_event_at,
        "driver_event_ids": risk.driver_event_ids,
    }


def ordered_patient_summaries(db: Session) -> list[dict[str, object]]:
    patients = db.execute(select(Patient)).scalars().all()
    summaries = [patient_summary(db, patient) for patient in patients]
    return sorted(
        summaries,
        key=lambda item: (
            SEVERITY_RANK.get(str(item["current_severity"]), 99),
            item["oldest_unresolved_event_at"] is None,
            item["oldest_unresolved_event_at"].timestamp() if item["oldest_unresolved_event_at"] else 0,
            -int(item["open_event_count"]),
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
