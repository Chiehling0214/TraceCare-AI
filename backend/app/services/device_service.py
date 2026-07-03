from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import ClinicalEvent
from app.services.risk_service import UNRESOLVED_STATUSES, all_patient_risks


DEVICE_PROTOCOL_VERSION = "tracecare-device-v1"


@dataclass(frozen=True)
class DeviceTargetState:
    state: str
    led: str
    buzzer: str
    derived_from_event_ids: list[int]


class SerialTransport(Protocol):
    def write_line(self, line: str) -> None:
        ...

    def read_line(self) -> str:
        ...

    def close(self) -> None:
        ...


class DeviceStateAdapter(ABC):
    mode: str

    @abstractmethod
    def current_state(self, db: Session) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def reconnect(self) -> dict[str, object]:
        raise NotImplementedError


class SimulatedDeviceStateAdapter(DeviceStateAdapter):
    mode = "simulated"

    def current_state(self, db: Session) -> dict[str, object]:
        return _state_payload(
            _target_state_from_events(db),
            adapter_mode=self.mode,
            connection="SIMULATED",
            connection_status="CONNECTED",
            hardware_available=False,
            fallback_active=False,
            last_heartbeat_at=None,
            last_command=None,
            last_error=None,
        )

    def health(self) -> dict[str, object]:
        return _health_payload(
            adapter_mode=self.mode,
            connection="SIMULATED",
            connection_status="CONNECTED",
            hardware_available=False,
            fallback_active=False,
            last_heartbeat_at=None,
            last_command=None,
            last_error=None,
        )

    def reconnect(self) -> dict[str, object]:
        return self.health()


class PySerialTransport:
    def __init__(self, port: str, baud_rate: int, timeout_seconds: float) -> None:
        try:
            import serial  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("SERIAL_DEPENDENCY_UNAVAILABLE") from exc
        self._serial = serial.Serial(port=port, baudrate=baud_rate, timeout=timeout_seconds)

    def write_line(self, line: str) -> None:
        self._serial.write((line.rstrip("\n") + "\n").encode("utf-8"))
        self._serial.flush()

    def read_line(self) -> str:
        return self._serial.readline().decode("utf-8", errors="replace").strip()

    def close(self) -> None:
        self._serial.close()


class USBSerialDeviceStateAdapter(DeviceStateAdapter):
    mode = "usb_serial"

    def __init__(
        self,
        port: str,
        baud_rate: int,
        timeout_seconds: float,
        heartbeat_timeout_seconds: float,
        transport: SerialTransport | None = None,
    ) -> None:
        self.port = port
        self.baud_rate = baud_rate
        self.timeout_seconds = timeout_seconds
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self._transport = transport
        self._provided_transport = transport
        self._sequence = 0
        self._connection_status = "DISCONNECTED"
        self._last_heartbeat_at: datetime | None = None
        self._last_command: str | None = None
        self._last_error: str | None = None

    def current_state(self, db: Session) -> dict[str, object]:
        target = _target_state_from_events(db)
        self._sync_target_state(target)
        return _state_payload(
            target,
            adapter_mode=self.mode,
            connection=_legacy_connection(self._connection_status),
            connection_status=self._connection_status,
            hardware_available=self._connection_status == "CONNECTED",
            fallback_active=self._connection_status != "CONNECTED",
            last_heartbeat_at=self._last_heartbeat_at,
            last_command=self._last_command,
            last_error=_public_error(self._last_error),
        )

    def health(self) -> dict[str, object]:
        self._heartbeat()
        return _health_payload(
            adapter_mode=self.mode,
            connection=_legacy_connection(self._connection_status),
            connection_status=self._connection_status,
            hardware_available=self._connection_status == "CONNECTED",
            fallback_active=self._connection_status != "CONNECTED",
            last_heartbeat_at=self._last_heartbeat_at,
            last_command=self._last_command,
            last_error=_public_error(self._last_error),
        )

    def reconnect(self) -> dict[str, object]:
        if self._transport is not None:
            try:
                self._transport.close()
            except Exception:
                pass
        self._transport = self._provided_transport
        self._connection_status = "RECONNECTING"
        self._last_error = None
        self._heartbeat()
        return _health_payload(
            adapter_mode=self.mode,
            connection=_legacy_connection(self._connection_status),
            connection_status=self._connection_status,
            hardware_available=self._connection_status == "CONNECTED",
            fallback_active=self._connection_status != "CONNECTED",
            last_heartbeat_at=self._last_heartbeat_at,
            last_command=self._last_command,
            last_error=_public_error(self._last_error),
        )

    def _sync_target_state(self, target: DeviceTargetState) -> None:
        if not self._heartbeat():
            return
        command = build_set_command(self._next_sequence(), target)
        self._send_expect(command, "ACK")

    def _heartbeat(self) -> bool:
        command = build_heartbeat_command(self._next_sequence())
        return self._send_expect(command, "PONG")

    def _send_expect(self, command: str, expected: str) -> bool:
        try:
            transport = self._ensure_transport()
            transport.write_line(command)
            self._last_command = command
            response = transport.read_line()
            if not _response_matches(response, expected):
                raise RuntimeError("DEVICE_PROTOCOL_ERROR")
            self._connection_status = "CONNECTED"
            self._last_error = None
            if expected == "PONG":
                self._last_heartbeat_at = datetime.now(timezone.utc)
            return True
        except Exception as exc:
            self._connection_status = "OFFLINE"
            self._last_error = _error_code(exc)
            return False

    def _ensure_transport(self) -> SerialTransport:
        if self._transport is None:
            if not self.port:
                raise RuntimeError("SERIAL_PORT_NOT_CONFIGURED")
            self._transport = PySerialTransport(self.port, self.baud_rate, self.timeout_seconds)
        return self._transport

    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence


def build_set_command(sequence: int, target: DeviceTargetState) -> str:
    return (
        f"SET seq={sequence} state={target.state} led={target.led} "
        f"buzzer={target.buzzer} protocol={DEVICE_PROTOCOL_VERSION}"
    )


def build_heartbeat_command(sequence: int) -> str:
    return f"PING seq={sequence} protocol={DEVICE_PROTOCOL_VERSION}"


def get_device_state(db: Session) -> dict[str, object]:
    return _get_adapter().current_state(db)


def get_device_health() -> dict[str, object]:
    return _get_adapter().health()


def reconnect_device() -> dict[str, object]:
    return _get_adapter().reconnect()


_adapter_cache: DeviceStateAdapter | None = None
_adapter_cache_key: tuple[object, ...] | None = None


def _get_adapter() -> DeviceStateAdapter:
    global _adapter_cache, _adapter_cache_key
    settings = get_settings()
    key = (
        settings.device_adapter_mode,
        settings.device_serial_port,
        settings.device_serial_baud_rate,
        settings.device_serial_timeout_seconds,
        settings.device_heartbeat_timeout_seconds,
    )
    if _adapter_cache is not None and _adapter_cache_key == key:
        return _adapter_cache
    if settings.device_adapter_mode == "usb_serial":
        _adapter_cache = USBSerialDeviceStateAdapter(
            settings.device_serial_port,
            settings.device_serial_baud_rate,
            settings.device_serial_timeout_seconds,
            settings.device_heartbeat_timeout_seconds,
        )
    else:
        _adapter_cache = SimulatedDeviceStateAdapter()
    _adapter_cache_key = key
    return _adapter_cache


def _target_state_from_events(db: Session) -> DeviceTargetState:
    risks = all_patient_risks(db)
    high_risk_ids = sorted(
        {event_id for risk in risks if risk.risk_state == "HIGH_RISK" for event_id in risk.driver_event_ids}
    )
    if high_risk_ids:
        return DeviceTargetState("CRITICAL", "RED_BLINKING", "INTERMITTENT", high_risk_ids)

    open_review_ids = _event_ids_by_status(db, ["OPEN"])
    if open_review_ids:
        return DeviceTargetState("WARNING", "YELLOW_BLINKING", "SHORT_BEEP", open_review_ids)

    acknowledged_ids = _event_ids_by_status(db, ["ACKNOWLEDGED", "DEFERRED"])
    if acknowledged_ids:
        return DeviceTargetState("ACKNOWLEDGED", "YELLOW_SOLID", "OFF", acknowledged_ids)

    return DeviceTargetState("NORMAL", "GREEN_SOLID", "OFF", [])


def _state_payload(
    target: DeviceTargetState,
    *,
    adapter_mode: str,
    connection: str,
    connection_status: str,
    hardware_available: bool,
    fallback_active: bool,
    last_heartbeat_at: datetime | None,
    last_command: str | None,
    last_error: str | None,
) -> dict[str, object]:
    payload = _health_payload(
        adapter_mode=adapter_mode,
        connection=connection,
        connection_status=connection_status,
        hardware_available=hardware_available,
        fallback_active=fallback_active,
        last_heartbeat_at=last_heartbeat_at,
        last_command=last_command,
        last_error=last_error,
    )
    return {
        **payload,
        "state": target.state,
        "led": target.led,
        "buzzer": target.buzzer,
        "derived_from_event_ids": target.derived_from_event_ids,
        "updated_at": datetime.now(timezone.utc),
    }


def _health_payload(
    *,
    adapter_mode: str,
    connection: str,
    connection_status: str,
    hardware_available: bool,
    fallback_active: bool,
    last_heartbeat_at: datetime | None,
    last_command: str | None,
    last_error: str | None,
) -> dict[str, object]:
    return {
        "adapter_mode": adapter_mode,
        "connection": connection,
        "connection_status": connection_status,
        "hardware_available": hardware_available,
        "fallback_active": fallback_active,
        "last_heartbeat_at": last_heartbeat_at,
        "last_command": last_command,
        "last_error": last_error,
        "protocol_version": DEVICE_PROTOCOL_VERSION,
    }


def _event_ids_by_status(db: Session, statuses: list[str]) -> list[int]:
    events = (
        db.query(ClinicalEvent)
        .filter(ClinicalEvent.status.in_(statuses), ClinicalEvent.status.in_(UNRESOLVED_STATUSES))
        .order_by(ClinicalEvent.created_at.asc(), ClinicalEvent.id.asc())
        .all()
    )
    return [event.id for event in events]


def _legacy_connection(connection_status: str) -> str:
    if connection_status == "CONNECTED":
        return "USB_SERIAL_CONNECTED"
    if connection_status == "RECONNECTING":
        return "USB_SERIAL_RECONNECTING"
    return "USB_SERIAL_OFFLINE"


def _response_matches(response: str, expected: str) -> bool:
    return response.strip().upper().startswith(expected)


def _error_code(exc: Exception) -> str:
    message = str(exc)
    if isinstance(exc, TimeoutError):
        return "DEVICE_TIMEOUT"
    if "SERIAL_PORT_NOT_CONFIGURED" in message:
        return "SERIAL_PORT_NOT_CONFIGURED"
    if "SERIAL_DEPENDENCY_UNAVAILABLE" in message:
        return "SERIAL_DEPENDENCY_UNAVAILABLE"
    if "DEVICE_PROTOCOL_ERROR" in message:
        return "DEVICE_PROTOCOL_ERROR"
    return "DEVICE_UNAVAILABLE"


def _public_error(error: str | None) -> str | None:
    return error
