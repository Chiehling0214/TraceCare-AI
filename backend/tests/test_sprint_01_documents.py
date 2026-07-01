from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClinicalDocument, ClinicalEvent, ClinicalFact, EventEvidence
from app.seed.synthetic import seed_synthetic_data


def _patient_id(client, code: str) -> int:
    payload = client.get("/api/patients").json()
    return next(item["id"] for item in payload["items"] if item["patient_code"] == code)


def test_synthetic_documents_seed_is_idempotent(db_session: Session):
    first = seed_synthetic_data(db_session)
    second = seed_synthetic_data(db_session)

    assert first["clinical_documents_created"] == 5
    assert first["clinical_facts_created"] == 5
    assert second["clinical_documents_created"] == 0
    assert second["clinical_facts_created"] == 0
    assert len(db_session.execute(select(ClinicalDocument)).scalars().all()) == 5
    assert len(db_session.execute(select(ClinicalFact)).scalars().all()) == 5


def test_document_and_fact_apis_include_source_positions(seeded_client):
    patient_id = _patient_id(seeded_client, "P001")

    documents = seeded_client.get(f"/api/patients/{patient_id}/documents")
    assert documents.status_code == 200
    assert documents.json()["total"] == 2
    assert documents.json()["items"][0]["is_synthetic"] is True

    document_id = documents.json()["items"][0]["id"]
    document = seeded_client.get(f"/api/documents/{document_id}")
    assert document.status_code == 200
    assert document.json()["source_document"].startswith("synthetic_")

    facts = seeded_client.get(f"/api/patients/{patient_id}/facts")
    assert facts.status_code == 200
    payload = facts.json()
    assert payload["total"] == 2
    assert {item["polarity"] for item in payload["items"]} == {"PRESENT", "NEGATED"}
    assert all(item["source_section"] for item in payload["items"])
    assert all(item["source_line"] > 0 for item in payload["items"])
    assert all(item["source_end_char"] > item["source_start_char"] for item in payload["items"])


def test_document_api_404_and_validation_errors(seeded_client):
    assert seeded_client.get("/api/patients/999/documents").status_code == 404
    assert seeded_client.get("/api/patients/999/facts").status_code == 404

    missing_document = seeded_client.get("/api/documents/999")
    assert missing_document.status_code == 404
    assert missing_document.json()["detail"]["error"]["code"] == "DOCUMENT_NOT_FOUND"

    invalid_document = seeded_client.get("/api/documents/not-an-int")
    assert invalid_document.status_code == 422


def test_p001_contradiction_analysis_creates_traceable_event(seeded_client):
    response = seeded_client.post("/api/prototype/run-contradiction-analysis")
    assert response.status_code == 200
    payload = response.json()
    p001 = next(item for item in payload["results"] if item["patient_code"] == "P001")
    assert p001["result"] == "EVENT_CREATED"
    assert p001["rule_id"] == "ALLERGY_CONTRADICTION"
    assert p001["subject"] == "penicillin"

    detail = seeded_client.get(f"/api/events/{p001['event_id']}").json()
    assert detail["event_type"] == "CONTRADICTION"
    assert detail["analysis"] is None
    assert detail["rule_id"] == "ALLERGY_CONTRADICTION"
    assert "Prototype rule triggered. Human review is required." in detail["description"]
    relation_types = {item["relation_type"] for item in detail["document_evidence"]}
    assert {"ASSERTED_FACT", "DENIED_FACT", "SOURCE_DOCUMENT", "SUPPORTS"} <= relation_types

    facts = [item["clinical_fact"] for item in detail["document_evidence"] if item["clinical_fact"]]
    assert {fact["polarity"] for fact in facts} == {"PRESENT", "NEGATED"}
    assert all(fact["document"]["source_document"].startswith("synthetic_") for fact in facts)
    assert all(fact["source_line"] > 0 for fact in facts)


def test_p002_and_p003_do_not_trigger_contradiction(seeded_client):
    payload = seeded_client.post("/api/prototype/run-contradiction-analysis").json()
    p002 = next(item for item in payload["results"] if item["patient_code"] == "P002")
    p003 = next(item for item in payload["results"] if item["patient_code"] == "P003")
    assert p002["result"] == "NO_TRIGGER"
    assert p003["result"] == "INSUFFICIENT_DATA"


def test_duplicate_contradiction_analysis_is_skipped(seeded_client, db_session: Session):
    first = seeded_client.post("/api/prototype/run-contradiction-analysis").json()
    second = seeded_client.post("/api/prototype/run-contradiction-analysis").json()
    assert first["events_created"] == 1
    assert second["events_created"] == 0
    assert second["events_skipped_as_duplicates"] == 1

    events = db_session.execute(
        select(ClinicalEvent).where(ClinicalEvent.rule_id == "ALLERGY_CONTRADICTION")
    ).scalars().all()
    assert len(events) == 1
    evidence = db_session.execute(
        select(EventEvidence).where(EventEvidence.event_id == events[0].id)
    ).scalars().all()
    assert len({(item.target_type, item.target_id, item.relation_type) for item in evidence}) == len(evidence)


def test_contradiction_events_use_existing_lifecycle_and_device_state(seeded_client):
    event_id = seeded_client.post("/api/prototype/run-contradiction-analysis").json()["results"][0]["event_id"]
    warning = seeded_client.get("/api/device-state").json()
    assert warning["state"] == "WARNING"
    assert event_id in warning["derived_from_event_ids"]

    acknowledged = seeded_client.post(f"/api/events/{event_id}/acknowledge")
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "ACKNOWLEDGED"

    resolved = seeded_client.post(f"/api/events/{event_id}/resolve")
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"
    assert seeded_client.get("/api/device-state").json()["state"] == "NORMAL"
