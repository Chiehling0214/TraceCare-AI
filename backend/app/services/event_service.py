from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ClinicalDocument, ClinicalEvent, ClinicalFact, EventEvidence, EvidenceLink, Patient
from app.services.errors import api_error


def get_event_or_404(db: Session, event_id: int) -> ClinicalEvent:
    event = db.execute(
        select(ClinicalEvent)
        .options(
            selectinload(ClinicalEvent.patient),
            selectinload(ClinicalEvent.patient).selectinload(Patient.clinical_documents),
            selectinload(ClinicalEvent.patient).selectinload(Patient.clinical_facts).selectinload(ClinicalFact.document),
            selectinload(ClinicalEvent.evidence_links).selectinload(EvidenceLink.lab_result),
            selectinload(ClinicalEvent.typed_evidence),
            selectinload(ClinicalEvent.actions),
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

    document_evidence = _build_document_evidence(event)

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
        "deferred_at": event.deferred_at,
        "deferred_until": event.deferred_until,
        "escalated_at": event.escalated_at,
        "escalation_reason": event.escalation_reason,
        "analysis": analysis,
        "evidence": evidence,
        "document_evidence": document_evidence,
        "action_history": sorted(event.actions, key=lambda item: (item.created_at, item.id)),
    }


def _build_document_evidence(event: ClinicalEvent) -> list[dict[str, object]]:
    typed_evidence = sorted(event.typed_evidence, key=lambda item: (item.relation_type, item.target_type, item.id))
    if not typed_evidence:
        return []

    fact_ids = [item.target_id for item in typed_evidence if item.target_type == "clinical_fact"]
    document_ids = [item.target_id for item in typed_evidence if item.target_type == "clinical_document"]

    facts: dict[int, ClinicalFact] = {}
    documents: dict[int, ClinicalDocument] = {}
    if fact_ids:
        for fact in event.patient.clinical_facts:
            if fact.id in fact_ids:
                facts[fact.id] = fact
                documents[fact.document.id] = fact.document
    if document_ids:
        for document in event.patient.clinical_documents:
            if document.id in document_ids:
                documents[document.id] = document

    def document_payload(document: ClinicalDocument) -> dict[str, object]:
        return {
            "id": document.id,
            "document_type": document.document_type,
            "title": document.title,
            "source_document": document.source_document,
            "authored_at": document.authored_at,
            "is_synthetic": document.is_synthetic,
        }

    items = []
    for evidence_item in typed_evidence:
        item: dict[str, object] = {
            "event_evidence_id": evidence_item.id,
            "target_type": evidence_item.target_type,
            "target_id": evidence_item.target_id,
            "relation_type": evidence_item.relation_type,
            "clinical_fact": None,
            "clinical_document": None,
        }
        if evidence_item.target_type == "clinical_fact" and evidence_item.target_id in facts:
            fact = facts[evidence_item.target_id]
            item["clinical_fact"] = {
                "id": fact.id,
                "fact_type": fact.fact_type,
                "subject": fact.subject,
                "polarity": fact.polarity,
                "value": fact.value,
                "status": fact.status,
                "source_section": fact.source_section,
                "source_line": fact.source_line,
                "source_start_char": fact.source_start_char,
                "source_end_char": fact.source_end_char,
                "observed_at": fact.observed_at,
                "document": document_payload(fact.document),
            }
        if evidence_item.target_type == "clinical_document" and evidence_item.target_id in documents:
            item["clinical_document"] = document_payload(documents[evidence_item.target_id])
        items.append(item)
    return items
