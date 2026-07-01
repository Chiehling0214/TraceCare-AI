from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analysis import AnalysisRunResponse
from app.schemas.device import DeviceStateResponse
from app.schemas.event import EventActionResponse, EventDetail, EventListResponse
from app.schemas.lab import LabListResponse
from app.schemas.patient import PatientDetail, PatientListResponse
from app.services import patient_service
from app.services.device_service import device_adapter
from app.services.errors import api_error
from app.services.event_service import acknowledge_event, build_event_detail, get_event_or_404, resolve_event
from app.services.rule_service import run_analysis

router = APIRouter(prefix="/api")


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


@router.get("/events/{event_id}", response_model=EventDetail, tags=["events"])
def get_event(event_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    return build_event_detail(get_event_or_404(db, event_id))


@router.post("/events/{event_id}/acknowledge", response_model=EventActionResponse, tags=["events"])
def post_acknowledge(event_id: int, db: Session = Depends(get_db)) -> object:
    return acknowledge_event(db, event_id)


@router.post("/events/{event_id}/resolve", response_model=EventActionResponse, tags=["events"])
def post_resolve(event_id: int, db: Session = Depends(get_db)) -> object:
    return resolve_event(db, event_id)


@router.post("/prototype/run-analysis", response_model=AnalysisRunResponse, tags=["analysis"])
def post_run_analysis(db: Session = Depends(get_db)) -> dict[str, object]:
    return run_analysis(db)


@router.get("/device-state", response_model=DeviceStateResponse, tags=["device"])
def get_device_state(db: Session = Depends(get_db)) -> dict[str, object]:
    return device_adapter.current_state(db)
