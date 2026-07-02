from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Patient
from app.services.contradiction_service import run_contradiction_analysis
from app.services.evidence_package_service import build_evidence_package
from app.services.lifecycle_service import acknowledge_event
from app.services.llm_adapter import FakeLLMAdapter, GeneratedSentence
from app.services.rule_service import run_analysis
from app.services.summary_service import generate_summary
from app.services.summary_validator import validate_summary_sentences


def _patient_id(db: Session, patient_code: str) -> int:
    return db.execute(select(Patient).where(Patient.patient_code == patient_code)).scalar_one().id


def _prepare_events(db: Session) -> int:
    run_analysis(db)
    run_contradiction_analysis(db)
    return _patient_id(db, "P001")


def test_evidence_package_contains_traceable_ids(seeded_client, db_session: Session):
    patient_id = _prepare_events(db_session)

    package = build_evidence_package(db_session, patient_id, "patient")

    evidence_ids = package.evidence_ids()
    assert package.sufficient is True
    assert f"patient:{patient_id}" in evidence_ids
    assert any(item.startswith("lab:") for item in evidence_ids)
    assert any(item.startswith("fact:") for item in evidence_ids)
    assert any(item.startswith("event:") for item in evidence_ids)
    assert f"risk:{patient_id}" in evidence_ids


def test_patient_summary_api_returns_validated_deterministic_fallback(seeded_client, db_session: Session):
    patient_id = _prepare_events(db_session)

    response = seeded_client.post(f"/api/patients/{patient_id}/summaries/patient", json={"prefer_llm": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "FALLBACK"
    assert payload["validation_status"] == "PASSED"
    assert payload["adapter_mode"] == "deterministic-fallback"
    assert payload["local_only"] is True
    assert payload["sentences"]
    assert all(sentence["evidence_ids"] for sentence in payload["sentences"])
    assert payload["evidence_package"]["sufficient"] is True

    summary_response = seeded_client.get(f"/api/summaries/{payload['id']}")
    assert summary_response.status_code == 200
    assert summary_response.json()["id"] == payload["id"]

    evidence_response = seeded_client.get(f"/api/summaries/{payload['id']}/evidence")
    assert evidence_response.status_code == 200
    assert evidence_response.json()["evidence_package"]["package_id"] == payload["evidence_package"]["package_id"]


def test_handoff_summary_uses_lifecycle_and_action_wording(seeded_client, db_session: Session):
    patient_id = _prepare_events(db_session)
    events = seeded_client.get(f"/api/patients/{patient_id}/events").json()["items"]
    acknowledge_event(db_session, events[0]["id"])

    response = seeded_client.post(f"/api/patients/{patient_id}/summaries/handoff", json={"prefer_llm": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "FALLBACK"
    assert payload["summary_kind"] == "handoff"
    assert "交班摘要" in payload["text"]
    assert any("action:" in evidence_id for sentence in payload["sentences"] for evidence_id in sentence["evidence_ids"])
    assert any(item["type"] == "action" for item in payload["evidence_package"]["evidence_items"])


def test_p003_summary_abstains_for_insufficient_evidence(seeded_client, db_session: Session):
    patient_id = _patient_id(db_session, "P003")

    response = seeded_client.post(f"/api/patients/{patient_id}/summaries/handoff")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ABSTAINED"
    assert payload["validation_status"] == "ABSTAINED"
    assert payload["sentences"] == []
    assert payload["abstention_reason"] == "INSUFFICIENT_LONGITUDINAL_SYNTHETIC_EVIDENCE"


def _assert_llm_validation_failure_falls_back(payload: dict):
    assert payload["status"] == "FALLBACK"
    assert payload["validation_status"] == "PASSED"
    assert payload["adapter_mode"] == "deterministic-fallback"
    assert payload["model_name"] is None
    assert payload["abstention_reason"] == "LLM_OUTPUT_VALIDATION_FAILED_FALLBACK_USED"
    assert payload["sentences"]
    assert payload["validation_errors"] == []


def test_generated_summary_with_missing_citation_falls_back(seeded_client, db_session: Session):
    patient_id = _prepare_events(db_session)
    adapter = FakeLLMAdapter([GeneratedSentence("Synthetic summary without citation.", [])])

    payload = generate_summary(db_session, patient_id, "patient", adapter=adapter)

    _assert_llm_validation_failure_falls_back(payload)
    package = build_evidence_package(db_session, patient_id, "patient")
    assert validate_summary_sentences(package, adapter.sentences) == ["SENTENCE_0_MISSING_CITATION"]


def test_generated_summary_with_unknown_citation_falls_back(seeded_client, db_session: Session):
    patient_id = _prepare_events(db_session)
    adapter = FakeLLMAdapter([GeneratedSentence("Synthetic summary with unknown source.", ["fact:999"])])

    payload = generate_summary(db_session, patient_id, "patient", adapter=adapter)

    _assert_llm_validation_failure_falls_back(payload)
    package = build_evidence_package(db_session, patient_id, "patient")
    assert validate_summary_sentences(package, adapter.sentences) == ["SENTENCE_0_UNKNOWN_EVIDENCE:fact:999"]


def test_generated_summary_with_numeric_mismatch_falls_back(seeded_client, db_session: Session):
    patient_id = _prepare_events(db_session)
    adapter = FakeLLMAdapter([GeneratedSentence("Creatinine was 9.9 mg/dL.", [f"patient:{patient_id}"])])

    payload = generate_summary(db_session, patient_id, "patient", adapter=adapter)

    _assert_llm_validation_failure_falls_back(payload)
    package = build_evidence_package(db_session, patient_id, "patient")
    assert "SENTENCE_0_NUMERIC_MISMATCH:9.9" in validate_summary_sentences(package, adapter.sentences)


def test_generated_summary_with_mentioned_uncited_evidence_falls_back(seeded_client, db_session: Session):
    patient_id = _prepare_events(db_session)
    adapter = FakeLLMAdapter([GeneratedSentence("This mentions event:2 without citing it.", [f"patient:{patient_id}"])])

    payload = generate_summary(db_session, patient_id, "patient", adapter=adapter)

    _assert_llm_validation_failure_falls_back(payload)
    package = build_evidence_package(db_session, patient_id, "patient")
    assert "SENTENCE_0_MENTIONED_EVIDENCE_NOT_CITED:event:2" in validate_summary_sentences(
        package, adapter.sentences
    )


def test_generated_summary_with_unsupported_contradiction_claim_falls_back(seeded_client, db_session: Session):
    patient_id = _prepare_events(db_session)
    adapter = FakeLLMAdapter(
        [
            GeneratedSentence(
                "Creatinine contradicts an allergy fact.",
                ["lab:2", "fact:2"],
            )
        ]
    )

    payload = generate_summary(db_session, patient_id, "patient", adapter=adapter)

    _assert_llm_validation_failure_falls_back(payload)
    package = build_evidence_package(db_session, patient_id, "patient")
    assert "SENTENCE_0_UNSUPPORTED_CONTRADICTION_CLAIM" in validate_summary_sentences(package, adapter.sentences)
