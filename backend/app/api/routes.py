from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.action import DeferEventRequest, EventActionsResponse
from app.schemas.analysis import AnalysisRunResponse, ContradictionAnalysisRunResponse
from app.schemas.device import DeviceHealthResponse, DeviceStateResponse
from app.schemas.document import ClinicalDocumentListResponse, ClinicalDocumentOut
from app.schemas.event import EventActionResponse, EventDetail, EventListResponse
from app.schemas.fact import ClinicalFactListResponse
from app.schemas.graph import EvidenceGraphResponse
from app.schemas.imports import DemoActionResponse, ImportCommitResponse, ImportErrorsResponse, ImportPayload, ImportPreviewResponse
from app.schemas.lab import LabListResponse
from app.schemas.patient import PatientDetail, PatientListResponse
from app.schemas.risk import PatientRiskResponse, RiskEvaluationRequest, RiskEvaluationResponse
from app.schemas.summary import SummaryEvidenceResponse, SummaryRequest, SummaryResponse
from app.services import document_service
from app.services import patient_service
from app.services.contradiction_service import run_contradiction_analysis
from app.services.device_service import get_device_health, get_device_state as build_device_state, reconnect_device
from app.services.errors import api_error
from app.services.event_service import build_event_detail, get_event_or_404
from app.services.graph_service import build_event_graph, build_patient_graph
from app.services.import_service import commit_documents, commit_labs, import_errors, preview_documents, preview_labs
from app.services.lifecycle_service import acknowledge_event, actions_for_event, defer_event, resolve_event
from app.services.demo_service import reset_demo, run_demo_analysis, seed_demo
from app.services.risk_service import patient_risk, run_risk_evaluation
from app.services.rule_service import run_analysis
from app.services.summary_service import generate_summary, get_summary, get_summary_evidence

router = APIRouter(prefix="/api")


def ensure_demo_management_enabled() -> None:
    if not get_settings().demo_management_enabled:
        raise api_error(403, "DEMO_MANAGEMENT_DISABLED", "Demo management endpoints are disabled.")


@router.get("/patients", response_model=PatientListResponse, tags=["patients"])
def list_patients(db: Session = Depends(get_db)) -> dict[str, object]:
    items = patient_service.ordered_patient_summaries(db)
    return {"items": items, "total": len(items)}


@router.get("/patients/{patient_id}", response_model=PatientDetail, tags=["patients"])
def get_patient(patient_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    patient = patient_service.get_patient(db, patient_id)
    if patient is None:
        raise api_error(404, "PATIENT_NOT_FOUND", f"Patient {patient_id} was not found.")
    summary = patient_service.patient_summary(db, patient)
    return {**summary, "created_at": patient.created_at}


@router.get("/patients/{patient_id}/labs", response_model=LabListResponse, tags=["labs"])
def list_patient_labs(patient_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    if patient_service.get_patient(db, patient_id) is None:
        raise api_error(404, "PATIENT_NOT_FOUND", f"Patient {patient_id} was not found.")
    items = patient_service.labs_for_patient(db, patient_id)
    return {"patient_id": patient_id, "items": items, "total": len(items)}


@router.get("/patients/{patient_id}/events", response_model=EventListResponse, tags=["events"])
def list_patient_events(patient_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    if patient_service.get_patient(db, patient_id) is None:
        raise api_error(404, "PATIENT_NOT_FOUND", f"Patient {patient_id} was not found.")
    items = patient_service.events_for_patient(db, patient_id)
    return {"patient_id": patient_id, "items": items, "total": len(items)}


@router.get("/patients/{patient_id}/risk", response_model=PatientRiskResponse, tags=["risk"])
def get_patient_risk(patient_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    return patient_risk(db, patient_id).as_dict()


@router.post(
    "/patients/{patient_id}/summaries/patient",
    response_model=SummaryResponse,
    tags=["summaries"],
)
def post_patient_summary(
    patient_id: int,
    payload: SummaryRequest | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return generate_summary(db, patient_id, "patient", prefer_llm=payload.prefer_llm if payload else True)


@router.post(
    "/patients/{patient_id}/summaries/handoff",
    response_model=SummaryResponse,
    tags=["summaries"],
)
def post_handoff_summary(
    patient_id: int,
    payload: SummaryRequest | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return generate_summary(db, patient_id, "handoff", prefer_llm=payload.prefer_llm if payload else True)


@router.get("/patients/{patient_id}/documents", response_model=ClinicalDocumentListResponse, tags=["documents"])
def list_patient_documents(patient_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    if patient_service.get_patient(db, patient_id) is None:
        raise api_error(404, "PATIENT_NOT_FOUND", f"Patient {patient_id} was not found.")
    items = document_service.documents_for_patient(db, patient_id)
    return {"patient_id": patient_id, "items": items, "total": len(items)}


@router.get("/documents/{document_id}", response_model=ClinicalDocumentOut, tags=["documents"])
def get_document(document_id: int, db: Session = Depends(get_db)) -> object:
    return document_service.get_document_or_404(db, document_id)


@router.get("/patients/{patient_id}/facts", response_model=ClinicalFactListResponse, tags=["documents"])
def list_patient_facts(patient_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    if patient_service.get_patient(db, patient_id) is None:
        raise api_error(404, "PATIENT_NOT_FOUND", f"Patient {patient_id} was not found.")
    items = document_service.facts_for_patient(db, patient_id)
    return {"patient_id": patient_id, "items": items, "total": len(items)}


@router.get("/events/{event_id}", response_model=EventDetail, tags=["events"])
def get_event(event_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    return build_event_detail(get_event_or_404(db, event_id))


@router.post("/events/{event_id}/acknowledge", response_model=EventActionResponse, tags=["events"])
def post_acknowledge(event_id: int, db: Session = Depends(get_db)) -> object:
    return acknowledge_event(db, event_id)


@router.post("/events/{event_id}/defer", response_model=EventActionResponse, tags=["events"])
def post_defer(event_id: int, payload: DeferEventRequest, db: Session = Depends(get_db)) -> object:
    return defer_event(
        db,
        event_id,
        reason=payload.reason,
        actor_label=payload.actor_label,
        defer_until=payload.defer_until,
    )


@router.post("/events/{event_id}/resolve", response_model=EventActionResponse, tags=["events"])
def post_resolve(event_id: int, db: Session = Depends(get_db)) -> object:
    return resolve_event(db, event_id)


@router.get("/events/{event_id}/actions", response_model=EventActionsResponse, tags=["events"])
def get_event_actions(event_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    items = actions_for_event(db, event_id)
    return {"event_id": event_id, "items": items, "total": len(items)}


@router.get("/summaries/{summary_id}", response_model=SummaryResponse, tags=["summaries"])
def get_summary_record(summary_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    return get_summary(db, summary_id)


@router.get("/summaries/{summary_id}/evidence", response_model=SummaryEvidenceResponse, tags=["summaries"])
def get_summary_record_evidence(summary_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    return get_summary_evidence(db, summary_id)


@router.post("/prototype/run-analysis", response_model=AnalysisRunResponse, tags=["analysis"])
def post_run_analysis(db: Session = Depends(get_db)) -> dict[str, object]:
    return run_analysis(db)


@router.post(
    "/prototype/run-contradiction-analysis",
    response_model=ContradictionAnalysisRunResponse,
    tags=["analysis"],
)
def post_run_contradiction_analysis(db: Session = Depends(get_db)) -> dict[str, object]:
    return run_contradiction_analysis(db)


@router.post(
    "/prototype/run-risk-evaluation",
    response_model=RiskEvaluationResponse,
    tags=["analysis", "risk"],
)
def post_run_risk_evaluation(
    payload: RiskEvaluationRequest | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return run_risk_evaluation(db, evaluated_at=payload.evaluated_at if payload else None)


@router.get("/patients/{patient_id}/evidence-graph", response_model=EvidenceGraphResponse, tags=["graph"])
def get_patient_evidence_graph(patient_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    return build_patient_graph(db, patient_id)


@router.get("/events/{event_id}/evidence-graph", response_model=EvidenceGraphResponse, tags=["graph"])
def get_event_evidence_graph(event_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    return build_event_graph(db, event_id)


@router.get("/device-state", response_model=DeviceStateResponse, tags=["device"])
def get_device_state(db: Session = Depends(get_db)) -> dict[str, object]:
    return build_device_state(db)


@router.get("/device/health", response_model=DeviceHealthResponse, tags=["device"])
def get_device_health_endpoint() -> dict[str, object]:
    return get_device_health()


@router.post("/device/reconnect", response_model=DeviceHealthResponse, tags=["device"])
def post_device_reconnect() -> dict[str, object]:
    return reconnect_device()


@router.post("/import/labs/preview", response_model=ImportPreviewResponse, tags=["import"])
def post_labs_preview(payload: ImportPayload, db: Session = Depends(get_db)) -> dict[str, object]:
    ensure_demo_management_enabled()
    return preview_labs(db, payload.source_filename, payload.content)


@router.post("/import/labs/commit", response_model=ImportCommitResponse, tags=["import"])
def post_labs_commit(payload: ImportPayload, db: Session = Depends(get_db)) -> dict[str, object]:
    ensure_demo_management_enabled()
    return commit_labs(db, payload.source_filename, payload.content)


@router.post("/import/documents/preview", response_model=ImportPreviewResponse, tags=["import"])
def post_documents_preview(payload: ImportPayload, db: Session = Depends(get_db)) -> dict[str, object]:
    ensure_demo_management_enabled()
    return preview_documents(db, payload.source_filename, payload.content)


@router.post("/import/documents/commit", response_model=ImportCommitResponse, tags=["import"])
def post_documents_commit(payload: ImportPayload, db: Session = Depends(get_db)) -> dict[str, object]:
    ensure_demo_management_enabled()
    return commit_documents(db, payload.source_filename, payload.content)


@router.get("/imports/{import_id}/errors", response_model=ImportErrorsResponse, tags=["import"])
def get_import_errors(import_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    ensure_demo_management_enabled()
    return import_errors(db, import_id)


@router.post("/development/reset-demo", response_model=DemoActionResponse, tags=["development"])
def post_reset_demo(db: Session = Depends(get_db)) -> dict[str, object]:
    ensure_demo_management_enabled()
    return reset_demo(db)


@router.post("/development/seed-demo", response_model=DemoActionResponse, tags=["development"])
def post_seed_demo(db: Session = Depends(get_db)) -> dict[str, object]:
    ensure_demo_management_enabled()
    return seed_demo(db)


@router.post("/development/run-demo-analysis", response_model=DemoActionResponse, tags=["development"])
def post_run_demo_analysis(db: Session = Depends(get_db)) -> dict[str, object]:
    ensure_demo_management_enabled()
    return run_demo_analysis(db)
