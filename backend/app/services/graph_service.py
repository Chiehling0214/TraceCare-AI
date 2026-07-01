from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ClinicalDocument, ClinicalEvent, ClinicalFact, EventEvidence, EvidenceLink, LabResult, Patient
from app.services.errors import api_error


def _node(nodes: dict[str, dict[str, Any]], node_id: str, node_type: str, label: str, **metadata: Any) -> None:
    nodes[node_id] = {"id": node_id, "type": node_type, "label": label, "metadata": metadata}


def _edge(
    edges: dict[str, dict[str, Any]],
    source: str,
    target: str,
    relation: str,
    **metadata: Any,
) -> None:
    edge_id = f"{source}->{target}:{relation}"
    edges[edge_id] = {"id": edge_id, "source": source, "target": target, "relation": relation, "metadata": metadata}


def build_patient_graph(db: Session, patient_id: int) -> dict[str, object]:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise api_error(404, "PATIENT_NOT_FOUND", f"Patient {patient_id} was not found.")

    labs = list(
        db.execute(select(LabResult).where(LabResult.patient_id == patient_id).order_by(LabResult.observed_at.asc()))
        .scalars()
        .all()
    )
    documents = list(
        db.execute(
            select(ClinicalDocument)
            .options(selectinload(ClinicalDocument.facts))
            .where(ClinicalDocument.patient_id == patient_id)
            .order_by(ClinicalDocument.authored_at.asc())
        )
        .scalars()
        .all()
    )
    events = list(
        db.execute(
            select(ClinicalEvent)
            .options(
                selectinload(ClinicalEvent.evidence_links).selectinload(EvidenceLink.lab_result),
                selectinload(ClinicalEvent.typed_evidence),
            )
            .where(ClinicalEvent.patient_id == patient_id)
            .order_by(ClinicalEvent.created_at.asc(), ClinicalEvent.id.asc())
        )
        .scalars()
        .all()
    )
    return _build_graph("patient", patient, labs, documents, events)


def build_event_graph(db: Session, event_id: int) -> dict[str, object]:
    event = db.execute(
        select(ClinicalEvent)
        .options(
            selectinload(ClinicalEvent.patient),
            selectinload(ClinicalEvent.evidence_links).selectinload(EvidenceLink.lab_result),
            selectinload(ClinicalEvent.typed_evidence),
        )
        .where(ClinicalEvent.id == event_id)
    ).scalar_one_or_none()
    if event is None:
        raise api_error(404, "EVENT_NOT_FOUND", f"Event {event_id} was not found.")

    labs = [link.lab_result for link in event.evidence_links]
    document_ids = [
        evidence.target_id for evidence in event.typed_evidence if evidence.target_type == "clinical_document"
    ]
    fact_ids = [evidence.target_id for evidence in event.typed_evidence if evidence.target_type == "clinical_fact"]
    facts = list(
        db.execute(
            select(ClinicalFact)
            .options(selectinload(ClinicalFact.document))
            .where(ClinicalFact.id.in_(fact_ids))
            .order_by(ClinicalFact.observed_at.asc(), ClinicalFact.id.asc())
        )
        .scalars()
        .all()
    )
    document_ids.extend(fact.document_id for fact in facts)
    documents = list(
        db.execute(
            select(ClinicalDocument)
            .options(selectinload(ClinicalDocument.facts))
            .where(ClinicalDocument.id.in_(set(document_ids)))
            .order_by(ClinicalDocument.authored_at.asc(), ClinicalDocument.id.asc())
        )
        .scalars()
        .all()
    )
    return _build_graph("event", event.patient, labs, documents, [event])


def _build_graph(
    scope: str,
    patient: Patient,
    labs: list[LabResult],
    documents: list[ClinicalDocument],
    events: list[ClinicalEvent],
) -> dict[str, object]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}

    patient_id = f"patient:{patient.id}"
    _node(nodes, patient_id, "patient", patient.patient_code, display_name=patient.display_name, is_synthetic=True)

    for lab in labs:
        lab_id = f"lab:{lab.id}"
        _node(
            nodes,
            lab_id,
            "lab",
            f"{lab.test_name} {lab.value:g} {lab.unit}",
            observed_at=lab.observed_at,
            source_document=lab.source_document,
        )
        _edge(edges, patient_id, lab_id, "HAS_LAB")

    for document in documents:
        document_id = f"document:{document.id}"
        _node(
            nodes,
            document_id,
            "document",
            document.title,
            document_type=document.document_type,
            source_document=document.source_document,
            authored_at=document.authored_at,
            is_synthetic=document.is_synthetic,
        )
        _edge(edges, patient_id, document_id, "HAS_DOCUMENT")
        for fact in sorted(document.facts, key=lambda item: (item.observed_at, item.id)):
            fact_id = f"fact:{fact.id}"
            _node(
                nodes,
                fact_id,
                "fact",
                f"{fact.subject}: {fact.polarity}",
                fact_type=fact.fact_type,
                subject=fact.subject,
                polarity=fact.polarity,
                value=fact.value,
                status=fact.status,
                source_section=fact.source_section,
                source_line=fact.source_line,
                source_start_char=fact.source_start_char,
                source_end_char=fact.source_end_char,
                observed_at=fact.observed_at,
            )
            _edge(edges, document_id, fact_id, "CONTAINS_FACT")

    for event in events:
        event_id = f"event:{event.id}"
        _node(
            nodes,
            event_id,
            "event",
            event.title,
            event_type=event.event_type,
            severity=event.severity,
            status=event.status,
            rule_id=event.rule_id,
            created_at=event.created_at,
        )
        _edge(edges, patient_id, event_id, "HAS_EVENT")
        for link in event.evidence_links:
            _edge(
                edges,
                f"lab:{link.lab_result_id}",
                event_id,
                link.relation_type,
                evidence_link_id=link.id,
            )
        for evidence in event.typed_evidence:
            if evidence.target_type == "clinical_fact":
                source = f"fact:{evidence.target_id}"
            elif evidence.target_type == "clinical_document":
                source = f"document:{evidence.target_id}"
            else:
                continue
            _edge(
                edges,
                source,
                event_id,
                evidence.relation_type,
                event_evidence_id=evidence.id,
            )

    return {"scope": scope, "nodes": list(nodes.values()), "edges": list(edges.values())}
