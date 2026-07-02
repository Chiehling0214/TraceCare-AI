from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClinicalEvent, EventAction
from app.services.errors import api_error
from app.services.event_service import get_event_or_404


DEFAULT_ACTOR = "prototype-reviewer"
DEFAULT_DEFER_HOURS = 4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def actions_for_event(db: Session, event_id: int) -> list[EventAction]:
    if db.get(ClinicalEvent, event_id) is None:
        raise api_error(404, "EVENT_NOT_FOUND", f"Event {event_id} was not found.")
    return list(
        db.execute(
            select(EventAction)
            .where(EventAction.event_id == event_id)
            .order_by(EventAction.created_at.asc(), EventAction.id.asc())
        )
        .scalars()
        .all()
    )


def acknowledge_event(
    db: Session,
    event_id: int,
    actor_label: str = DEFAULT_ACTOR,
    note: str | None = None,
    now: datetime | None = None,
) -> ClinicalEvent:
    event = get_event_or_404(db, event_id)
    if event.status == "RESOLVED":
        raise api_error(409, "INVALID_EVENT_TRANSITION", "A resolved event cannot be acknowledged.")
    if event.status in {"OPEN", "DEFERRED"}:
        timestamp = now or utc_now()
        event.status = "ACKNOWLEDGED"
        event.acknowledged_at = event.acknowledged_at or timestamp
        _record_action(db, event, "ACKNOWLEDGE", actor_label, note, timestamp)
        db.commit()
        db.refresh(event)
    return event


def defer_event(
    db: Session,
    event_id: int,
    reason: str,
    actor_label: str = DEFAULT_ACTOR,
    defer_until: datetime | None = None,
    now: datetime | None = None,
) -> ClinicalEvent:
    event = get_event_or_404(db, event_id)
    if event.status == "RESOLVED":
        raise api_error(409, "INVALID_EVENT_TRANSITION", "A resolved event cannot be deferred.")
    timestamp = now or utc_now()
    event.status = "DEFERRED"
    event.deferred_at = timestamp
    event.deferred_until = defer_until or (timestamp + timedelta(hours=DEFAULT_DEFER_HOURS))
    _record_action(db, event, "DEFER", actor_label, reason, timestamp)
    db.commit()
    db.refresh(event)
    return event


def resolve_event(
    db: Session,
    event_id: int,
    actor_label: str = DEFAULT_ACTOR,
    note: str | None = None,
    now: datetime | None = None,
) -> ClinicalEvent:
    event = get_event_or_404(db, event_id)
    if event.status == "RESOLVED":
        raise api_error(409, "INVALID_EVENT_TRANSITION", "The event is already resolved.")
    timestamp = now or utc_now()
    if event.acknowledged_at is None:
        event.acknowledged_at = timestamp
    event.status = "RESOLVED"
    event.resolved_at = timestamp
    _record_action(db, event, "RESOLVE", actor_label, note, timestamp)
    db.commit()
    db.refresh(event)
    return event


def _record_action(
    db: Session,
    event: ClinicalEvent,
    action_type: str,
    actor_label: str,
    note: str | None,
    created_at: datetime,
) -> EventAction:
    action = EventAction(
        event_id=event.id,
        patient_id=event.patient_id,
        action_type=action_type,
        actor_label=actor_label,
        note=note,
        created_at=created_at,
    )
    db.add(action)
    return action
