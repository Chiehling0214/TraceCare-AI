from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LabResult, Patient
from app.seed.synthetic import seed_synthetic_data


def _patient_id(client, code: str) -> int:
    payload = client.get("/api/patients").json()
    return next(item["id"] for item in payload["items"] if item["patient_code"] == code)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_seed_is_idempotent(db_session: Session):
    first = seed_synthetic_data(db_session)
    second = seed_synthetic_data(db_session)
    assert first["patients_created"] == 3
    assert first["lab_results_created"] == 5
    assert second["patients_created"] == 0
    assert second["lab_results_created"] == 0
    assert len(db_session.execute(select(Patient)).scalars().all()) == 3
    assert len(db_session.execute(select(LabResult)).scalars().all()) == 5


def test_p001_triggers_rapid_increase(seeded_client):
    response = seeded_client.post("/api/prototype/run-analysis")
    assert response.status_code == 200
    payload = response.json()
    p001 = next(item for item in payload["results"] if item["patient_code"] == "P001")
    assert p001["result"] == "EVENT_CREATED"
    assert p001["rule_id"] == "RAPID_INCREASE"

    events = seeded_client.get(f"/api/patients/{p001['patient_id']}/events").json()
    assert events["total"] == 1
    assert events["items"][0]["severity"] == "REVIEW_REQUIRED"


def test_p002_and_p003_do_not_trigger(seeded_client):
    response = seeded_client.post("/api/prototype/run-analysis")
    payload = response.json()
    p002 = next(item for item in payload["results"] if item["patient_code"] == "P002")
    p003 = next(item for item in payload["results"] if item["patient_code"] == "P003")
    assert p002["result"] == "NO_TRIGGER"
    assert p003["result"] == "INSUFFICIENT_DATA"


def test_duplicate_analysis_is_skipped(seeded_client):
    first = seeded_client.post("/api/prototype/run-analysis").json()
    second = seeded_client.post("/api/prototype/run-analysis").json()
    assert first["events_created"] == 1
    assert second["events_created"] == 0
    assert second["events_skipped_as_duplicates"] == 1


def test_event_detail_includes_evidence(seeded_client):
    result = seeded_client.post("/api/prototype/run-analysis").json()
    event_id = next(item["event_id"] for item in result["results"] if item["patient_code"] == "P001")
    response = seeded_client.get(f"/api/events/{event_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rule_id"] == "RAPID_INCREASE"
    assert payload["analysis"]["previous_value"] == 0.8
    assert payload["analysis"]["current_value"] == 1.3
    relation_types = {item["relation_type"] for item in payload["evidence"]}
    assert {"PREVIOUS_VALUE", "CURRENT_VALUE", "SUPPORTS"} <= relation_types
    assert "synthetic_lab_report_20260621.csv" in {
        item["lab_result"]["source_document"] for item in payload["evidence"]
    }


def test_acknowledge_and_resolve_update_status_and_timestamps(seeded_client):
    event_id = seeded_client.post("/api/prototype/run-analysis").json()["results"][0]["event_id"]
    acknowledged = seeded_client.post(f"/api/events/{event_id}/acknowledge")
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "ACKNOWLEDGED"
    assert acknowledged.json()["acknowledged_at"] is not None

    resolved = seeded_client.post(f"/api/events/{event_id}/resolve")
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"
    assert resolved.json()["resolved_at"] is not None


def test_device_state_follows_event_lifecycle(seeded_client):
    seeded_client.post("/api/prototype/run-analysis")
    event_id = seeded_client.get(f"/api/patients/{_patient_id(seeded_client, 'P001')}/events").json()["items"][0]["id"]
    warning = seeded_client.get("/api/device-state").json()
    assert warning["state"] == "WARNING"
    assert warning["led"] == "YELLOW_BLINKING"
    assert warning["buzzer"] == "SHORT_BEEP"

    seeded_client.post(f"/api/events/{event_id}/acknowledge")
    acknowledged = seeded_client.get("/api/device-state").json()
    assert acknowledged["state"] == "ACKNOWLEDGED"
    assert acknowledged["buzzer"] == "OFF"

    seeded_client.post(f"/api/events/{event_id}/resolve")
    normal = seeded_client.get("/api/device-state").json()
    assert normal["state"] == "NORMAL"
    assert normal["led"] == "GREEN_SOLID"


def test_unknown_patient_and_event_return_404(seeded_client):
    patient_response = seeded_client.get("/api/patients/999")
    assert patient_response.status_code == 404
    assert patient_response.json()["detail"]["error"]["code"] == "PATIENT_NOT_FOUND"

    event_response = seeded_client.get("/api/events/999")
    assert event_response.status_code == 404
    assert event_response.json()["detail"]["error"]["code"] == "EVENT_NOT_FOUND"
