from abc import ABC, abstractmethod
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClinicalEvent


class DeviceStateAdapter(ABC):
    @abstractmethod
    def current_state(self, db: Session) -> dict[str, object]:
        raise NotImplementedError


class SimulatedDeviceStateAdapter(DeviceStateAdapter):
    connection = "SIMULATED"

    def current_state(self, db: Session) -> dict[str, object]:
        events = list(
            db.execute(
                select(ClinicalEvent)
                .where(ClinicalEvent.status.in_(["OPEN", "ACKNOWLEDGED"]))
                .order_by(ClinicalEvent.created_at.desc())
            )
            .scalars()
            .all()
        )
        open_high = [event for event in events if event.status == "OPEN" and event.severity == "HIGH_RISK"]
        if open_high:
            return self._state("CRITICAL", "RED_BLINKING", "INTERMITTENT", open_high)

        open_review = [event for event in events if event.status == "OPEN" and event.severity == "REVIEW_REQUIRED"]
        if open_review:
            return self._state("WARNING", "YELLOW_BLINKING", "SHORT_BEEP", open_review)

        acknowledged = [event for event in events if event.status == "ACKNOWLEDGED"]
        if acknowledged:
            return self._state("ACKNOWLEDGED", "YELLOW_SOLID", "OFF", acknowledged)

        return self._state("NORMAL", "GREEN_SOLID", "OFF", [])

    def _state(self, state: str, led: str, buzzer: str, events: list[ClinicalEvent]) -> dict[str, object]:
        return {
            "connection": self.connection,
            "state": state,
            "led": led,
            "buzzer": buzzer,
            "derived_from_event_ids": [event.id for event in events],
            "updated_at": datetime.now(timezone.utc),
        }


device_adapter: DeviceStateAdapter = SimulatedDeviceStateAdapter()
