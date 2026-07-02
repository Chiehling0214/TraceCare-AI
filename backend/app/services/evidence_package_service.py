from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ClinicalDocument, ClinicalEvent, ClinicalFact, EventAction, LabResult, Patient
from app.services.errors import api_error
from app.services.risk_service import patient_risk


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    type: str
    label: str
    text: str
    numeric_values: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "text": self.text,
            "numeric_values": self.numeric_values,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EvidencePackage:
    package_id: str
    patient_id: int
    patient_code: str
    summary_kind: str
    evidence_items: list[EvidenceItem]
    sufficient: bool
    insufficiency_reason: str | None = None

    def evidence_ids(self) -> set[str]:
        return {item.id for item in self.evidence_items}

    def item_map(self) -> dict[str, EvidenceItem]:
        return {item.id: item for item in self.evidence_items}

    def as_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "patient_id": self.patient_id,
            "patient_code": self.patient_code,
            "summary_kind": self.summary_kind,
            "evidence_items": [item.as_dict() for item in self.evidence_items],
            "sufficient": self.sufficient,
            "insufficiency_reason": self.insufficiency_reason,
        }


def build_evidence_package(db: Session, patient_id: int, summary_kind: str) -> EvidencePackage:
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
            .order_by(ClinicalDocument.authored_at.asc(), ClinicalDocument.id.asc())
        )
        .scalars()
        .all()
    )
    facts = list(
        db.execute(
            select(ClinicalFact)
            .options(selectinload(ClinicalFact.document))
            .where(ClinicalFact.patient_id == patient_id)
            .order_by(ClinicalFact.observed_at.asc(), ClinicalFact.id.asc())
        )
        .scalars()
        .all()
    )
    events = list(
        db.execute(
            select(ClinicalEvent)
            .where(ClinicalEvent.patient_id == patient_id)
            .order_by(ClinicalEvent.created_at.asc(), ClinicalEvent.id.asc())
        )
        .scalars()
        .all()
    )
    actions = list(
        db.execute(
            select(EventAction)
            .where(EventAction.patient_id == patient_id)
            .order_by(EventAction.created_at.asc(), EventAction.id.asc())
        )
        .scalars()
        .all()
    )

    items: list[EvidenceItem] = [
        EvidenceItem(
            id=f"patient:{patient.id}",
            type="patient",
            label=patient.patient_code,
            text=f"{patient.patient_code} is {patient.display_name}, a synthetic TraceCare AI patient.",
            metadata={"display_name": patient.display_name, "is_synthetic": True},
        )
    ]

    for lab in labs:
        items.append(
            EvidenceItem(
                id=f"lab:{lab.id}",
                type="lab",
                label=f"{lab.test_name} {lab.value:g} {lab.unit}",
                text=(
                    f"{lab.test_name} was {lab.value:g} {lab.unit} with reference range "
                    f"{lab.reference_min:g}-{lab.reference_max:g} {lab.unit} from {lab.source_document}."
                ),
                numeric_values=[_number(lab.value), _number(lab.reference_min), _number(lab.reference_max)],
                metadata={
                    "test_name": lab.test_name,
                    "value": lab.value,
                    "unit": lab.unit,
                    "observed_at": lab.observed_at.isoformat(),
                    "source_document": lab.source_document,
                },
            )
        )

    for document in documents:
        items.append(
            EvidenceItem(
                id=f"document:{document.id}",
                type="document",
                label=document.title,
                text=f"{document.title} is a synthetic {document.document_type} from {document.source_document}.",
                metadata={
                    "document_type": document.document_type,
                    "source_document": document.source_document,
                    "authored_at": document.authored_at.isoformat(),
                    "is_synthetic": document.is_synthetic,
                },
            )
        )

    for fact in facts:
        items.append(
            EvidenceItem(
                id=f"fact:{fact.id}",
                type="fact",
                label=f"{fact.subject}: {fact.polarity}",
                text=(
                    f"Structured fact states '{fact.value}' with polarity {fact.polarity} in "
                    f"{fact.document.source_document}, section {fact.source_section}, line {fact.source_line}."
                ),
                numeric_values=[str(fact.source_line), str(fact.source_start_char), str(fact.source_end_char)],
                metadata={
                    "fact_type": fact.fact_type,
                    "subject": fact.subject,
                    "polarity": fact.polarity,
                    "status": fact.status,
                    "document_id": fact.document_id,
                    "source_section": fact.source_section,
                    "source_line": fact.source_line,
                    "source_start_char": fact.source_start_char,
                    "source_end_char": fact.source_end_char,
                },
            )
        )

    for event in events:
        items.append(
            EvidenceItem(
                id=f"event:{event.id}",
                type="event",
                label=event.title,
                text=(
                    f"Prototype event {event.event_type} has severity {event.severity}, status {event.status}, "
                    f"rule {event.rule_id}, and title '{event.title}'."
                ),
                numeric_values=[],
                metadata={
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "status": event.status,
                    "rule_id": event.rule_id,
                    "created_at": event.created_at.isoformat(),
                },
            )
        )

    for action in actions:
        items.append(
            EvidenceItem(
                id=f"action:{action.id}",
                type="action",
                label=f"{action.action_type} for event {action.event_id}",
                text=(
                    f"Prototype lifecycle action {action.action_type} was recorded for event {action.event_id} "
                    f"by {action.actor_label}."
                ),
                numeric_values=[],
                metadata={
                    "event_id": action.event_id,
                    "action_type": action.action_type,
                    "actor_label": action.actor_label,
                    "note": action.note,
                    "created_at": action.created_at.isoformat(),
                },
            )
        )

    risk = patient_risk(db, patient_id)
    items.append(
        EvidenceItem(
            id=f"risk:{patient.id}",
            type="risk",
            label=f"Deterministic risk {risk.risk_state}",
            text=(
                f"Deterministic Sprint 2 risk state is {risk.risk_state} with "
                f"{risk.unresolved_event_count} unresolved event(s)."
            ),
            numeric_values=[str(risk.unresolved_event_count)],
            metadata={
                "risk_state": risk.risk_state,
                "risk_reasons": [reason.code for reason in risk.risk_reasons],
                "driver_event_ids": risk.driver_event_ids,
            },
        )
    )

    sufficient = len(labs) >= 2 and len(documents) >= 2
    reason = None if sufficient else "INSUFFICIENT_LONGITUDINAL_SYNTHETIC_EVIDENCE"
    return EvidencePackage(
        package_id=f"patient:{patient.id}:{summary_kind}",
        patient_id=patient.id,
        patient_code=patient.patient_code,
        summary_kind=summary_kind,
        evidence_items=items,
        sufficient=sufficient,
        insufficiency_reason=reason,
    )


def _number(value: float) -> str:
    return f"{value:g}"
