from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClinicalEvent, EventAction, Patient
from app.services.errors import api_error


TIMEOUT_HOURS = 2.0
UNRESOLVED_STATUSES = ["OPEN", "ACKNOWLEDGED", "DEFERRED"]
RISK_RANK = {"HIGH_RISK": 0, "REVIEW_REQUIRED": 1, "NORMAL": 2}


@dataclass(frozen=True)
class RiskReason:
    code: str
    message: str
    event_ids: list[int]


@dataclass(frozen=True)
class PatientRisk:
    patient_id: int
    patient_code: str
    risk_state: str
    risk_reasons: list[RiskReason]
    unresolved_event_count: int
    oldest_unresolved_event_at: datetime | None
    driver_event_ids: list[int]

    def as_dict(self) -> dict[str, object]:
        return {
            "patient_id": self.patient_id,
            "patient_code": self.patient_code,
            "risk_state": self.risk_state,
            "risk_reasons": [
                {"code": reason.code, "message": reason.message, "event_ids": reason.event_ids}
                for reason in self.risk_reasons
            ],
            "unresolved_event_count": self.unresolved_event_count,
            "oldest_unresolved_event_at": self.oldest_unresolved_event_at,
            "driver_event_ids": self.driver_event_ids,
        }


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def unresolved_events_for_patient(db: Session, patient_id: int) -> list[ClinicalEvent]:
    return list(
        db.execute(
            select(ClinicalEvent)
            .where(ClinicalEvent.patient_id == patient_id, ClinicalEvent.status.in_(UNRESOLVED_STATUSES))
            .order_by(ClinicalEvent.created_at.asc(), ClinicalEvent.id.asc())
        )
        .scalars()
        .all()
    )


def calculate_patient_risk(patient: Patient, events: list[ClinicalEvent], now: datetime | None = None) -> PatientRisk:
    evaluated_at = now or utc_now()
    unresolved = [event for event in events if event.status in UNRESOLVED_STATUSES]
    if not unresolved:
        return PatientRisk(patient.id, patient.patient_code, "NORMAL", [], 0, None, [])

    reasons: list[RiskReason] = []
    driver_ids: set[int] = set()

    high_events = [event for event in unresolved if event.severity == "HIGH_RISK"]
    if high_events:
        ids = [event.id for event in high_events]
        driver_ids.update(ids)
        reasons.append(
            RiskReason(
                "HIGH_RISK_EVENT",
                "One or more unresolved prototype events are marked HIGH_RISK.",
                ids,
            )
        )

    open_events = [event for event in unresolved if event.status == "OPEN"]
    timed_out = [event for event in open_events if _event_age_hours(event, evaluated_at) >= TIMEOUT_HOURS]
    if timed_out:
        ids = [event.id for event in timed_out]
        driver_ids.update(ids)
        reasons.append(
            RiskReason(
                "UNACKNOWLEDGED_TIMEOUT",
                f"Open prototype event age reached {TIMEOUT_HOURS:g} hours.",
                ids,
            )
        )

    active_event_types = {event.event_type for event in unresolved}
    if len(active_event_types) >= 2:
        ids = [event.id for event in unresolved]
        driver_ids.update(ids)
        reasons.append(
            RiskReason(
                "MULTIPLE_EVENT_TYPES",
                "Multiple unresolved prototype event types are present for the same synthetic patient.",
                ids,
            )
        )

    deferred = [event for event in unresolved if event.status == "DEFERRED"]
    if deferred:
        ids = [event.id for event in deferred]
        reasons.append(RiskReason("DEFERRED_EVENT", "Deferred events remain unresolved and visible.", ids))

    acknowledged = [event for event in unresolved if event.status == "ACKNOWLEDGED"]
    if acknowledged:
        ids = [event.id for event in acknowledged]
        reasons.append(RiskReason("ACKNOWLEDGED_UNRESOLVED", "Acknowledged events remain unresolved.", ids))

    if not reasons:
        ids = [event.id for event in unresolved]
        driver_ids.update(ids)
        reasons.append(RiskReason("UNRESOLVED_EVENTS", "Unresolved prototype events require review.", ids))

    risk_state = "HIGH_RISK" if any(reason.code in {"HIGH_RISK_EVENT", "UNACKNOWLEDGED_TIMEOUT", "MULTIPLE_EVENT_TYPES"} for reason in reasons) else "REVIEW_REQUIRED"
    oldest = min((event.created_at for event in unresolved), default=None)
    return PatientRisk(
        patient.id,
        patient.patient_code,
        risk_state,
        reasons,
        len(unresolved),
        oldest,
        sorted(driver_ids or {event.id for event in unresolved}),
    )


def patient_risk(db: Session, patient_id: int, now: datetime | None = None) -> PatientRisk:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise api_error(404, "PATIENT_NOT_FOUND", f"Patient {patient_id} was not found.")
    return calculate_patient_risk(patient, unresolved_events_for_patient(db, patient_id), now=now)


def all_patient_risks(db: Session, now: datetime | None = None) -> list[PatientRisk]:
    patients = list(db.execute(select(Patient).order_by(Patient.patient_code.asc())).scalars().all())
    return [calculate_patient_risk(patient, unresolved_events_for_patient(db, patient.id), now=now) for patient in patients]


def run_risk_evaluation(db: Session, evaluated_at: datetime | None = None) -> dict[str, object]:
    now = evaluated_at or utc_now()
    events = list(
        db.execute(
            select(ClinicalEvent)
            .where(ClinicalEvent.status == "OPEN")
            .order_by(ClinicalEvent.created_at.asc(), ClinicalEvent.id.asc())
        )
        .scalars()
        .all()
    )
    escalated = 0
    for event in events:
        if _event_age_hours(event, now) < TIMEOUT_HOURS:
            continue
        if event.severity != "HIGH_RISK":
            event.severity = "HIGH_RISK"
            escalated += 1
        event.escalated_at = event.escalated_at or now
        event.escalation_reason = f"Prototype timeout: OPEN for at least {TIMEOUT_HOURS:g} hours."
        _record_auto_escalation_once(db, event, now)

    results = [risk.as_dict() for risk in all_patient_risks(db, now=now)]
    db.commit()
    return {
        "evaluation_run_id": f"prototype-risk-{now.strftime('%Y%m%dT%H%M%SZ')}",
        "evaluated_at": now,
        "patients_evaluated": len(results),
        "events_escalated": escalated,
        "results": results,
    }


def _event_age_hours(event: ClinicalEvent, now: datetime) -> float:
    return (_ensure_aware(now) - _ensure_aware(event.created_at)).total_seconds() / 3600


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _record_auto_escalation_once(db: Session, event: ClinicalEvent, now: datetime) -> None:
    exists = db.execute(
        select(EventAction).where(EventAction.event_id == event.id, EventAction.action_type == "AUTO_ESCALATE")
    ).scalar_one_or_none()
    if exists:
        return
    db.add(
        EventAction(
            event_id=event.id,
            patient_id=event.patient_id,
            action_type="AUTO_ESCALATE",
            actor_label="prototype-system",
            note=event.escalation_reason,
            created_at=now,
        )
    )
