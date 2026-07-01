from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EventEvidence(Base):
    __tablename__ = "event_evidence"
    __table_args__ = (
        UniqueConstraint("event_id", "target_type", "target_id", "relation_type", name="uq_event_typed_evidence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("clinical_events.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(64), index=True)
    target_id: Mapped[int] = mapped_column(Integer, index=True)
    relation_type: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    event = relationship("ClinicalEvent", back_populates="typed_evidence")
