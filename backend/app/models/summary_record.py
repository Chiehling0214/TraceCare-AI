from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SummaryRecord(Base):
    __tablename__ = "summary_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    summary_kind: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    validation_status: Mapped[str] = mapped_column(String(32), index=True)
    adapter_mode: Mapped[str] = mapped_column(String(32))
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    local_only: Mapped[str] = mapped_column(String(8), default="true")
    text: Mapped[str] = mapped_column(Text)
    sentences_json: Mapped[str] = mapped_column(Text)
    evidence_package_json: Mapped[str] = mapped_column(Text)
    validation_errors_json: Mapped[str] = mapped_column(Text, default="[]")
    abstention_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
