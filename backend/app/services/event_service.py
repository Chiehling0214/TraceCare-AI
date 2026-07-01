from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ClinicalEvent, EvidenceLink
from app.services.errors import api_error


def get_event_or_404(db: Session, event_id: int) -> ClinicalEvent:
    event = db.execute(
        select(ClinicalEvent)
        .options(
            selectinload(ClinicalEvent.patient),
            selectinload(ClinicalEvent.evidence_links).selectinload(EvidenceLink.lab_result),
        )
        .where(ClinicalEvent.id == event_id)
    ).scalar_one_or_none()
    if event is None:
        raise api_error(404, "EVENT_NOT_FOUND", f"Event {event_id} was not found.")
    return event


def acknowledge_event(db: Session, event_id: int) -> ClinicalEvent:
    event = get_event_or_404(db, event_id)
    if event.status == "RESOLVED":
        raise api_error(409, "INVALID_EVENT_TRANSITION", "A resolved event cannot be acknowledged.")
    if event.status == "OPEN":
        event.status = "ACKNOWLEDGED"
        event.acknowledged_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(event)
    return event


def resolve_event(db: Session, event_id: int) -> ClinicalEvent:
    event = get_event_or_404(db, event_id)
    if event.status == "RESOLVED":
        raise api_error(409, "INVALID_EVENT_TRANSITION", "The event is already resolved.")
    if event.acknowledged_at is None:
        event.acknowledged_at = datetime.now(timezone.utc)
    event.status = "RESOLVED"
    event.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)
    return event


def build_event_detail(event: ClinicalEvent) -> dict[str, object]:
    evidence = []
    previous = None
    current = None
    for link in sorted(event.evidence_links, key=lambda item: (item.relation_type, item.id)):
        lab = link.lab_result
        item = {
            "evidence_link_id": link.id,
            "relation_type": link.relation_type,
            "lab_result": {
                "id": lab.id,
                "test_name": lab.test_name,
                "value": lab.value,
                "unit": lab.unit,
                "observed_at": lab.observed_at,
                "source_document": lab.source_document,
            },
        }
        evidence.append(item)
        if link.relation_type == "PREVIOUS_VALUE":
            previous = lab
        if link.relation_type == "CURRENT_VALUE":
            current = lab

    analysis = None
    if previous and current:
        analysis = {
            "test_name": current.test_name,
            "previous_value": previous.value,
            "current_value": current.value,
            "unit": current.unit,
            "previous_observed_at": previous.observed_at,
            "current_observed_at": current.observed_at,
            "time_difference_hours": (current.observed_at - previous.observed_at).total_seconds() / 3600,
        }

    return {
        "id": event.id,
        "patient": {
            "id": event.patient.id,
            "patient_code": event.patient.patient_code,
            "display_name": event.patient.display_name,
            "is_synthetic": True,
        },
        "event_type": event.event_type,
        "severity": event.severity,
        "status": event.status,
        "title": event.title,
        "description": event.description,
        "rule_id": event.rule_id,
        "created_at": event.created_at,
        "acknowledged_at": event.acknowledged_at,
        "resolved_at": event.resolved_at,
        "analysis": analysis,
        "evidence": evidence,
    }
