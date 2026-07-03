from sqlalchemy.orm import Session

from app.services.device_service import (
    DeviceTargetState,
    USBSerialDeviceStateAdapter,
    build_heartbeat_command,
    build_set_command,
)
from app.services.rule_service import run_analysis


class FakeSerialTransport:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.writes: list[str] = []
        self.closed = False

    def write_line(self, line: str) -> None:
        self.writes.append(line)

    def read_line(self) -> str:
        if not self.responses:
            raise TimeoutError("fake timeout")
        return self.responses.pop(0)

    def close(self) -> None:
        self.closed = True


def test_sprint_4_simulated_device_state_keeps_backward_compatible_fields(seeded_client):
    seeded_client.post("/api/prototype/run-analysis")

    response = seeded_client.get("/api/device-state")

    assert response.status_code == 200
    payload = response.json()
    assert payload["connection"] == "SIMULATED"
    assert payload["adapter_mode"] == "simulated"
    assert payload["connection_status"] == "CONNECTED"
    assert payload["hardware_available"] is False
    assert payload["fallback_active"] is False
    assert payload["state"] == "WARNING"
    assert payload["led"] == "YELLOW_BLINKING"
    assert payload["buzzer"] == "SHORT_BEEP"
    assert payload["protocol_version"] == "tracecare-device-v1"


def test_sprint_4_device_health_and_reconnect_are_available_in_simulated_mode(seeded_client):
    health = seeded_client.get("/api/device/health")
    reconnect = seeded_client.post("/api/device/reconnect")

    assert health.status_code == 200
    assert reconnect.status_code == 200
    assert health.json()["adapter_mode"] == "simulated"
    assert reconnect.json()["connection_status"] == "CONNECTED"


def test_sprint_4_serial_command_builders_are_deterministic():
    command = build_heartbeat_command(7)
    assert command == "PING seq=7 protocol=tracecare-device-v1"
    target = DeviceTargetState("NORMAL", "GREEN_SOLID", "OFF", [])
    assert build_set_command(8, target) == (
        "SET seq=8 state=NORMAL led=GREEN_SOLID buzzer=OFF protocol=tracecare-device-v1"
    )


def test_sprint_4_fake_serial_receives_heartbeat_and_state_command(seeded_client, db_session: Session):
    run_analysis(db_session)
    transport = FakeSerialTransport(["PONG seq=1", "ACK seq=2"])
    adapter = USBSerialDeviceStateAdapter("FAKE", 115200, 1.0, 3.0, transport=transport)

    payload = adapter.current_state(db_session)

    assert payload["adapter_mode"] == "usb_serial"
    assert payload["connection_status"] == "CONNECTED"
    assert payload["hardware_available"] is True
    assert payload["fallback_active"] is False
    assert payload["state"] == "WARNING"
    assert transport.writes[0] == "PING seq=1 protocol=tracecare-device-v1"
    assert transport.writes[1] == (
        "SET seq=2 state=WARNING led=YELLOW_BLINKING buzzer=SHORT_BEEP protocol=tracecare-device-v1"
    )


def test_sprint_4_serial_offline_uses_laptop_fallback(seeded_client, db_session: Session):
    run_analysis(db_session)
    transport = FakeSerialTransport([])
    adapter = USBSerialDeviceStateAdapter("FAKE", 115200, 1.0, 3.0, transport=transport)

    payload = adapter.current_state(db_session)

    assert payload["connection"] == "USB_SERIAL_OFFLINE"
    assert payload["connection_status"] == "OFFLINE"
    assert payload["hardware_available"] is False
    assert payload["fallback_active"] is True
    assert payload["last_error"] == "DEVICE_TIMEOUT"
    assert payload["last_command"] == "PING seq=1 protocol=tracecare-device-v1"
    assert payload["state"] == "WARNING"
    assert payload["led"] == "YELLOW_BLINKING"


def test_sprint_4_serial_reconnect_uses_safe_repeat_heartbeat():
    transport = FakeSerialTransport(["PONG seq=1", "PONG seq=2"])
    adapter = USBSerialDeviceStateAdapter("FAKE", 115200, 1.0, 3.0, transport=transport)

    first = adapter.health()
    second = adapter.reconnect()

    assert first["connection_status"] == "CONNECTED"
    assert second["connection_status"] == "CONNECTED"
    assert transport.closed is True
    assert transport.writes == [
        "PING seq=1 protocol=tracecare-device-v1",
        "PING seq=2 protocol=tracecare-device-v1",
    ]


def test_sprint_4_set_command_is_idempotent_safe_for_repeats():
    target = DeviceTargetState("CRITICAL", "RED_BLINKING", "INTERMITTENT", [1, 2])

    first = build_set_command(11, target)
    repeated = build_set_command(12, target)

    assert "state=CRITICAL" in first
    assert "led=RED_BLINKING" in first
    assert "buzzer=INTERMITTENT" in first
    assert repeated.replace("seq=12", "seq=11") == first
