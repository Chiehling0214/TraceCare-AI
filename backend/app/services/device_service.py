from abc import ABC, abstractmethod
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import ClinicalEvent
from app.services.risk_service import UNRESOLVED_STATUSES, all_patient_risks


class DeviceStateAdapter(ABC):
    @abstractmethod
    def current_state(self, db: Session) -> dict[str, object]:
        raise NotImplementedError


class SimulatedDeviceStateAdapter(DeviceStateAdapter):
    connection = "SIMULATED"

    def current_state(self, db: Session) -> dict[str, object]:
        risks = all_patient_risks(db)
        high_risk_ids = sorted({event_id for risk in risks if risk.risk_state == "HIGH_RISK" for event_id in risk.driver_event_ids})
        if high_risk_ids:
            return self._state("CRITICAL", "RED_BLINKING", "INTERMITTENT", high_risk_ids)

        open_review_ids = _event_ids_by_status(db, ["OPEN"])
        if open_review_ids:
            return self._state("WARNING", "YELLOW_BLINKING", "SHORT_BEEP", open_review_ids)

        acknowledged_ids = _event_ids_by_status(db, ["ACKNOWLEDGED", "DEFERRED"])
        if acknowledged_ids:
            return self._state("ACKNOWLEDGED", "YELLOW_SOLID", "OFF", acknowledged_ids)

        return self._state("NORMAL", "GREEN_SOLID", "OFF", [])

    def _state(self, state: str, led: str, buzzer: str, event_ids: list[int]) -> dict[str, object]:
        return {
            "connection": self.connection,
            "state": state,
            "led": led,
            "buzzer": buzzer,
            "derived_from_event_ids": event_ids,
            "updated_at": datetime.now(timezone.utc),
        }


device_adapter: DeviceStateAdapter = SimulatedDeviceStateAdapter()


def _event_ids_by_status(db: Session, statuses: list[str]) -> list[int]:
    events = (
        db.query(ClinicalEvent)
        .filter(ClinicalEvent.status.in_(statuses), ClinicalEvent.status.in_(UNRESOLVED_STATUSES))
        .order_by(ClinicalEvent.created_at.asc(), ClinicalEvent.id.asc())
        .all()
    )
    return [event.id for event in events]
