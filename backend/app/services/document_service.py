from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ClinicalDocument, ClinicalFact
from app.services.errors import api_error


def documents_for_patient(db: Session, patient_id: int) -> list[ClinicalDocument]:
    return list(
        db.execute(
            select(ClinicalDocument)
            .where(ClinicalDocument.patient_id == patient_id)
            .order_by(ClinicalDocument.authored_at.asc(), ClinicalDocument.id.asc())
        )
        .scalars()
        .all()
    )


def get_document_or_404(db: Session, document_id: int) -> ClinicalDocument:
    document = db.execute(
        select(ClinicalDocument).options(selectinload(ClinicalDocument.facts)).where(ClinicalDocument.id == document_id)
    ).scalar_one_or_none()
    if document is None:
        raise api_error(404, "DOCUMENT_NOT_FOUND", f"Document {document_id} was not found.")
    return document


def facts_for_patient(db: Session, patient_id: int) -> list[ClinicalFact]:
    return list(
        db.execute(
            select(ClinicalFact)
            .where(ClinicalFact.patient_id == patient_id)
            .order_by(ClinicalFact.observed_at.asc(), ClinicalFact.id.asc())
        )
        .scalars()
        .all()
    )
