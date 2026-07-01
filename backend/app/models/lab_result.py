from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LabResult(Base):
    __tablename__ = "lab_results"
    __table_args__ = (
        UniqueConstraint("patient_id", "test_name", "observed_at", "source_document", name="uq_lab_seed_identity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    test_name: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    reference_min: Mapped[float] = mapped_column(Float)
    reference_max: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_document: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    patient = relationship("Patient", back_populates="lab_results")
    evidence_links = relationship("EvidenceLink", back_populates="lab_result", cascade="all, delete-orphan")
