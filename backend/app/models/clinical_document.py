from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClinicalDocument(Base):
    __tablename__ = "clinical_documents"
    __table_args__ = (UniqueConstraint("patient_id", "source_document", name="uq_document_seed_identity"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    document_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(180))
    source_document: Mapped[str] = mapped_column(String(255))
    authored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)

    patient = relationship("Patient", back_populates="clinical_documents")
    facts = relationship("ClinicalFact", back_populates="document", cascade="all, delete-orphan")
