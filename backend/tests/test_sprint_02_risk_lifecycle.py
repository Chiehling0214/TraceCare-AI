from datetime import datetime, timedelta, timezone

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.models import ClinicalEvent, EventAction


def _patient_id(client, code: str) -> int:
    payload = client.get("/api/patients").json()
    return next(item["id"] for item in payload["items"] if item["patient_code"] == code)


def _p001_event_ids(client) -> list[int]:
    patient_id = _patient_id(client, "P001")
    return [item["id"] for item in client.get(f"/api/patients/{patient_id}/events").json()["items"]]


def test_sprint_2_tables_and_columns_exist(db_session: Session):
    inspector = inspect(db_session.get_bind())
    assert "event_actions" in inspector.get_table_names()
    clinical_event_columns = {column["name"] for column in inspector.get_columns("clinical_events")}
    assert {"deferred_at", "deferred_until", "escalated_at", "escalation_reason"} <= clinical_event_columns


def test_risk_fusion_makes_p001_high_risk_and_explainable(seeded_client):
    seeded_client.post("/api/prototype/run-analysis")
    seeded_client.post("/api/prototype/run-contradiction-analysis")

    patient_id = _patient_id(seeded_client, "P001")
    risk = seeded_client.get(f"/api/patients/{patient_id}/risk")
    assert risk.status_code == 200
    payload = risk.json()
    assert payload["risk_state"] == "HIGH_RISK"
    assert payload["unresolved_event_count"] == 2
    assert "MULTIPLE_EVENT_TYPES" in {reason["code"] for reason in payload["risk_reasons"]}
    assert len(payload["driver_event_ids"]) == 2

    patients = seeded_client.get("/api/patients").json()["items"]
    assert patients[0]["patient_code"] == "P001"
    assert patients[0]["current_severity"] == "HIGH_RISK"
    assert patients[0]["risk_reasons"]


def test_defer_records_action_and_keeps_event_visible(seeded_client):
    event_id = seeded_client.post("/api/prototype/run-analysis").json()["results"][0]["event_id"]
    response = seeded_client.post(
        f"/api/events/{event_id}/defer",
        json={
            "reason": "Prototype reviewer needs later follow-up.",
            "defer_until": "2026-06-21T13:00:00Z",
            "actor_label": "synthetic-reviewer-a",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "DEFERRED"
    assert payload["deferred_at"] is not None
    assert payload["deferred_until"].startswith("2026-06-21T13:00:00")

    patient_id = _patient_id(seeded_client, "P001")
    events = seeded_client.get(f"/api/patients/{patient_id}/events").json()
    assert events["total"] == 1
    assert events["items"][0]["status"] == "DEFERRED"

    actions = seeded_client.get(f"/api/events/{event_id}/actions").json()
    assert actions["total"] == 1
    assert actions["items"][0]["action_type"] == "DEFER"
    assert actions["items"][0]["actor_label"] == "synthetic-reviewer-a"

    device = seeded_client.get("/api/device-state").json()
    assert device["state"] == "ACKNOWLEDGED"
    assert event_id in device["derived_from_event_ids"]


def test_deferred_event_can_be_acknowledged_and_resolved_with_history(seeded_client):
    event_id = seeded_client.post("/api/prototype/run-analysis").json()["results"][0]["event_id"]
    seeded_client.post(f"/api/events/{event_id}/defer", json={"reason": "Need later prototype review."})

    acknowledged = seeded_client.post(f"/api/events/{event_id}/acknowledge")
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "ACKNOWLEDGED"

    resolved = seeded_client.post(f"/api/events/{event_id}/resolve")
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"

    actions = seeded_client.get(f"/api/events/{event_id}/actions").json()["items"]
    assert [item["action_type"] for item in actions] == ["DEFER", "ACKNOWLEDGE", "RESOLVE"]

    detail = seeded_client.get(f"/api/events/{event_id}").json()
    assert [item["action_type"] for item in detail["action_history"]] == ["DEFER", "ACKNOWLEDGE", "RESOLVE"]


def test_timeout_risk_evaluation_escalates_once_and_records_audit(seeded_client, db_session: Session):
    event_id = seeded_client.post("/api/prototype/run-analysis").json()["results"][0]["event_id"]
    event = db_session.get(ClinicalEvent, event_id)
    event.created_at = datetime(2026, 6, 21, 8, 0, tzinfo=timezone.utc)
    db_session.commit()

    evaluation = seeded_client.post(
        "/api/prototype/run-risk-evaluation",
        json={"evaluated_at": "2026-06-21T11:00:00Z"},
    )
    assert evaluation.status_code == 200
    payload = evaluation.json()
    assert payload["events_escalated"] == 1
    p001 = next(item for item in payload["results"] if item["patient_code"] == "P001")
    assert p001["risk_state"] == "HIGH_RISK"
    assert "UNACKNOWLEDGED_TIMEOUT" in {reason["code"] for reason in p001["risk_reasons"]}

    detail = seeded_client.get(f"/api/events/{event_id}").json()
    assert detail["severity"] == "HIGH_RISK"
    assert detail["escalated_at"] is not None
    assert "Prototype timeout" in detail["escalation_reason"]
    assert [item["action_type"] for item in detail["action_history"]] == ["AUTO_ESCALATE"]

    second = seeded_client.post(
        "/api/prototype/run-risk-evaluation",
        json={"evaluated_at": "2026-06-21T12:00:00Z"},
    ).json()
    assert second["events_escalated"] == 0
    actions = db_session.execute(
        select(EventAction).where(EventAction.event_id == event_id, EventAction.action_type == "AUTO_ESCALATE")
    ).scalars().all()
    assert len(actions) == 1


def test_defer_and_actions_error_paths(seeded_client):
    event_id = seeded_client.post("/api/prototype/run-analysis").json()["results"][0]["event_id"]
    seeded_client.post(f"/api/events/{event_id}/resolve")

    response = seeded_client.post(f"/api/events/{event_id}/defer", json={"reason": "Too late."})
    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "INVALID_EVENT_TRANSITION"

    missing_actions = seeded_client.get("/api/events/999/actions")
    assert missing_actions.status_code == 404
