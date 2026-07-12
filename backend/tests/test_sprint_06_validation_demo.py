from app.sprint6_validation import run_validation


def _patient_id(client, code: str) -> int:
    payload = client.get("/api/patients").json()
    return next(item["id"] for item in payload["items"] if item["patient_code"] == code)


def test_sprint_6_validation_runner_produces_expected_metrics():
    report = run_validation()

    assert report["dataset_id"] == "tracecare-sprint6-validation-v1"
    assert report["setup"]["seed_idempotent"] is True
    assert report["metrics"]["rapid_increase_rule"]["f1"] == 1.0
    assert report["metrics"]["contradiction_detection"]["f1"] == 1.0
    assert report["metrics"]["event_state_synchronization"]["success_rate"] == 1.0
    assert report["metrics"]["summary_validation"]["validation_failure_rate"] == 0.0
    assert report["metrics"]["device_state"]["success_rate"] == 1.0


def test_sprint_6_api_level_demo_flow(client):
    assert client.post("/api/development/reset-demo").json()["status"] == "RESET"
    seed = client.post("/api/development/seed-demo").json()
    assert seed["status"] == "SEEDED"
    duplicate_seed = client.post("/api/development/seed-demo").json()
    assert duplicate_seed["patients_created"] == 0

    analysis = client.post("/api/development/run-demo-analysis").json()
    assert analysis["status"] == "ANALYZED"
    assert analysis["events_created"] >= 3

    p001_id = _patient_id(client, "P001")
    detail = client.get(f"/api/patients/{p001_id}").json()
    assert detail["patient_code"] == "P001"
    assert detail["current_severity"] == "HIGH_RISK"

    graph = client.get(f"/api/patients/{p001_id}/evidence-graph").json()
    assert graph["nodes"]
    assert graph["edges"]

    events = client.get(f"/api/patients/{p001_id}/events").json()["items"]
    event_id = events[0]["id"]
    assert client.post(f"/api/events/{event_id}/acknowledge").json()["status"] == "ACKNOWLEDGED"
    assert client.post(f"/api/events/{event_id}/resolve").json()["status"] == "RESOLVED"
    actions = client.get(f"/api/events/{event_id}/actions").json()
    assert [item["action_type"] for item in actions["items"]] == ["ACKNOWLEDGE", "RESOLVE"]

    summary = client.post(f"/api/patients/{p001_id}/summaries/patient", json={"prefer_llm": False}).json()
    assert summary["validation_status"] == "PASSED"
    assert all(sentence["evidence_ids"] for sentence in summary["sentences"])

    device = client.get("/api/device-state").json()
    assert device["adapter_mode"] == "simulated"
    assert device["state"] in {"CRITICAL", "WARNING", "ACKNOWLEDGED", "NORMAL"}

