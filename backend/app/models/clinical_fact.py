from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClinicalFact(Base):
    __tablename__ = "clinical_facts"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "fact_type",
            "subject",
            "polarity",
            "source_line",
            "source_start_char",
            "source_end_char",
            name="uq_fact_seed_identity",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("clinical_documents.id"), index=True)
    fact_type: Mapped[str] = mapped_column(String(64), index=True)
    subject: Mapped[str] = mapped_column(String(120), index=True)
    polarity: Mapped[str] = mapped_column(String(32), index=True)
    value: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), index=True)
    source_section: Mapped[str] = mapped_column(String(120))
    source_line: Mapped[int] = mapped_column(Integer)
    source_start_char: Mapped[int] = mapped_column(Integer)
    source_end_char: Mapped[int] = mapped_column(Integer)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    patient = relationship("Patient", back_populates="clinical_facts")
    document = relationship("ClinicalDocument", back_populates="facts")
