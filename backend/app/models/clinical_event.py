from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClinicalEvent(Base):
    __tablename__ = "clinical_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    rule_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deferred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deferred_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    patient = relationship("Patient", back_populates="clinical_events")
    evidence_links = relationship("EvidenceLink", back_populates="event", cascade="all, delete-orphan")
    typed_evidence = relationship("EventEvidence", back_populates="event", cascade="all, delete-orphan")
    actions = relationship("EventAction", back_populates="event", cascade="all, delete-orphan")


class EvidenceLink(Base):
    __tablename__ = "evidence_links"
    __table_args__ = (
        UniqueConstraint("event_id", "lab_result_id", "relation_type", name="uq_event_lab_relation"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("clinical_events.id"), index=True)
    lab_result_id: Mapped[int] = mapped_column(ForeignKey("lab_results.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(32), index=True)

    event = relationship("ClinicalEvent", back_populates="evidence_links")
    lab_result = relationship("LabResult", back_populates="evidence_links")
