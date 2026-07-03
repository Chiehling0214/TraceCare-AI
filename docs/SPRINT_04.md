# Sprint 4: ESP32 and Physical Alerting

## Status

In Progress

## Background

Sprint 0 includes a simulated device adapter that maps event state to LED and buzzer state. Sprint 4 adds optional physical hardware while preserving simulation so the demo remains runnable without ESP32.

## Goal

Add a USB Serial ESP32 adapter, heartbeat/offline handling, reconnect support, laptop fallback alerting, and firmware for LEDs and buzzer, without controlling any medical device.

## User Stories

- As a demo operator with hardware, I can see LED and buzzer changes match dashboard state.
- As a demo operator without hardware, I can run the full demo in simulated mode.
- As a reviewer, I can see when the physical device is disconnected.
- As a developer, I can test device state mapping without ESP32.

## Scope

- Add USB Serial adapter behind existing device adapter boundary.
- Preserve simulated adapter.
- Add heartbeat command/response.
- Add offline/reconnect states.
- Add laptop sound/visual fallback.
- Add firmware for green/yellow/red LEDs and active buzzer.
- Sync device state after acknowledge/defer/resolve actions.

## Non-goals

- No control of medical devices.
- No control of infusion pumps, ventilators, or treatment devices.
- No Bluetooth/Wi-Fi device integration.
- No hardware requirement for core dashboard demo.

## Dependencies

- Sprint 0 device adapter boundary.
- Sprint 2 unified risk/lifecycle is preferred for final alert priority.

## Current Repository Assessment

- `device_service.py` already defines an abstract adapter and simulated implementation.
- Device state currently reads event status directly.
- No serial dependency exists.
- Firmware directory exists at `firmware/esp32_tracecare_alert`.
- Frontend displays a simulated device panel only.

## Proposed Architecture Changes

- Add configurable adapter selection: `SIMULATED` or `USB_SERIAL`.
- Keep adapter implementations isolated from event/risk services.
- Add device health service for connection/heartbeat state.
- Add fallback alert service in frontend or backend API response.

## Proposed Data Model Changes

Optional additive table:

- Device status history:
  - adapter type
  - connection status
  - last heartbeat
  - last command
  - last error
  - created time

If not persisted, expose transient status through API only.

## Proposed API Changes

Add or extend:

- `GET /api/device-state` with adapter type, connection status, heartbeat time.
- `POST /api/device/reconnect`
- `GET /api/device/health`

Exact shape TBD after Sprint 2 risk output.

## Proposed UI Changes

- Device panel shows simulated/USB mode.
- Device panel shows connected/offline/reconnecting.
- Dashboard shows laptop fallback alert when hardware is offline.
- No fake hardware controls unless they map to real reconnect/test behavior.

## Synthetic Test Data

- Use Sprint 0/2 event states to trigger normal, warning, critical, acknowledged.
- Add fake serial adapter tests with simulated responses/timeouts.

## Tasks

1. Define serial command protocol.
2. Add USB Serial adapter.
3. Add adapter selection config.
4. Add heartbeat/offline/reconnect logic.
5. Add firmware sketch.
6. Add fake serial tests.
7. Update frontend device panel.
8. Document hardware wiring and fallback mode.

## Expected Files

- backend serial adapter module.
- backend fake serial tests.
- firmware directory for ESP32 sketch.
- frontend device health UI updates.
- hardware setup documentation.

## Migration Strategy

- No database migration required unless status history is persisted.
- Simulated adapter remains default.
- Hardware config must be optional.

## Testing Plan

- Existing device state tests remain passing.
- Fake serial adapter receives correct commands for each state.
- Offline heartbeat produces offline state.
- Dashboard remains usable when serial adapter fails.
- Firmware command protocol documented and manually smoke-tested.

## Acceptance Criteria

- Simulated mode still works with no hardware.
- USB Serial mode can drive LED/buzzer states.
- Offline hardware does not block dashboard alerts.
- Human acknowledgement updates dashboard and device state.

## Risks and Mitigations

- Risk: serial port availability differs by OS.
  - Mitigation: keep simulation default and document port config.
- Risk: hardware failure disrupts demo.
  - Mitigation: laptop fallback and visible offline state.
- Risk: alert appears to control treatment.
  - Mitigation: label as non-medical alert device only.

## Definition of Done

- Adapter selection is configurable.
- Simulation and serial modes are tested.
- Firmware exists and protocol is documented.
- UI shows hardware health and fallback state.

## Implemented

- Preserved the existing simulated device state behavior and backward-compatible `GET /api/device-state` fields.
- Added configurable device adapter mode:
  - `simulated`
  - `usb_serial`
- Added USB Serial adapter boundary with:
  - lazy `pyserial` transport,
  - heartbeat command,
  - state sync command,
  - reconnect behavior,
  - sanitized offline/error state.
- Added transient device health APIs:
  - `GET /api/device/health`
  - `POST /api/device/reconnect`
- Added frontend device health panel fields:
  - adapter mode,
  - connection status,
  - heartbeat time,
  - fallback state,
  - sanitized error code,
  - reconnect button calling backend API.
- Added fake serial transport tests for heartbeat, state commands, offline fallback, reconnect, and idempotent command behavior.
- Added command protocol documentation in `docs/DEVICE_PROTOCOL.md`.
- Added ESP32 firmware sketch at `firmware/esp32_tracecare_alert/esp32_tracecare_alert.ino`.

## Device Adapter Architecture

Device state is still derived from existing Sprint 0 through Sprint 2 event/risk services:

- `NORMAL` -> `GREEN_SOLID` / `OFF`
- `WARNING` -> `YELLOW_BLINKING` / `SHORT_BEEP`
- `ACKNOWLEDGED` -> `YELLOW_SOLID` / `OFF`
- `CRITICAL` -> `RED_BLINKING` / `INTERMITTENT`

The API route layer calls device service functions only. Serial port and heartbeat logic live inside `USBSerialDeviceStateAdapter`.

`simulated` remains the default adapter mode and requires no hardware.

## Configuration

```text
DEVICE_ADAPTER_MODE=simulated
DEVICE_SERIAL_PORT=
DEVICE_SERIAL_BAUD_RATE=115200
DEVICE_SERIAL_TIMEOUT_SECONDS=1.0
DEVICE_HEARTBEAT_TIMEOUT_SECONDS=3.0
```

No COM port is hard-coded. Docker Compose forwards these environment variables into the backend container.

## Serial Command Protocol

Protocol version: `tracecare-device-v1`

Heartbeat:

```text
PING seq=1 protocol=tracecare-device-v1
PONG seq=1 status=OK protocol=tracecare-device-v1
```

State sync:

```text
SET seq=2 state=WARNING led=YELLOW_BLINKING buzzer=SHORT_BEEP protocol=tracecare-device-v1
ACK seq=2 status=OK protocol=tracecare-device-v1
```

`SET` is idempotent and safe to repeat. Firmware should set the requested state rather than toggling from previous state.

## Acceptance Results

- Simulated mode still works with no hardware: PASS.
- USB Serial mode can drive LED/buzzer states: PASS in fake serial transport tests; NOT VERIFIED with real ESP32 hardware.
- Offline hardware does not block dashboard alerts: PASS in fake serial/offline fallback tests.
- Human acknowledgement updates dashboard and device state: PASS through existing Sprint 0/Sprint 2 lifecycle regression tests.
- Heartbeat with real ESP32: NOT VERIFIED.
- Disconnect/reconnect with real ESP32: NOT VERIFIED.
- Physical LED and buzzer output: NOT VERIFIED.

## Test Results

- Baseline backend tests displayed all tests through `[100%]`; pytest process did not exit cleanly in the current Windows shell, matching previous local behavior.
- Sprint 4 backend tests displayed `7 passed`.
- Frontend build passed using the existing sandbox `esbuild spawn EPERM` workaround.
- Serial port environment check via `Get-CimInstance Win32_SerialPort` failed with OS access denied, so real hardware availability could not be confirmed.
- Firmware compile tools were not available: `arduino-cli` and `pio` commands were not found.
- `python -m compileall` could not write existing `__pycache__` files in the current workspace, but backend tests and Docker runtime imports succeeded.

## Deviations

- Device status history is not persisted. Sprint 4 exposes transient health through API responses because persistence is optional in the sprint spec and no later API currently needs historical device records.
- Real ESP32 hardware was not verified because the current environment could not access serial port enumeration.
- The firmware sketch is duplicated in `docs/DEVICE_PROTOCOL.md` for setup readability, with the source `.ino` tracked under `firmware/esp32_tracecare_alert/`.

## Technical Decisions

- `GET /api/device-state` remains backward-compatible and adds fields instead of renaming existing ones.
- Serial errors are reduced to sanitized frontend-safe error codes such as `SERIAL_PORT_NOT_CONFIGURED`, `SERIAL_DEPENDENCY_UNAVAILABLE`, `DEVICE_TIMEOUT`, and `DEVICE_PROTOCOL_ERROR`.
- Missing serial configuration or heartbeat failure returns backend-derived device state with `fallback_active=true`.
- Frontend reconnect never mutates local hardware state directly; it calls `POST /api/device/reconnect` and reloads backend state.

## Known Issues

- Real ESP32 LED, buzzer, heartbeat, disconnect, and reconnect behavior remain `NOT VERIFIED`.
- The current prototype still uses SQLAlchemy `create_all` plus additive helpers rather than a formal migration framework.

## Next Sprint Dependency

Sprint 6 depends on Sprint 4 for hardware latency and synchronization metrics. If Sprint 4 hardware is not available, Sprint 6 must mark hardware metrics as simulated-only.
