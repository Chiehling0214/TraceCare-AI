# Sprint 10: ESP32 Hardware Verification

## Status

Planned

## Background

Sprint 4 added a serial device adapter, heartbeat/reconnect/fallback behavior, and ESP32 firmware. Sprint 6 validated simulated device behavior but did not verify real ESP32 hardware in the final validation run.

Sprint 10 focuses only on real hardware verification and documentation.

## Goal

Verify the ESP32 alert device end-to-end with the backend serial adapter while preserving simulated mode as the default safe fallback.

## User Stories

- As a presenter, I can show physical LED/buzzer response when hardware is available.
- As a demo operator, I can recover when the ESP32 is disconnected.
- As a reviewer, I can distinguish simulated device behavior from real hardware verification.
- As a developer, I can test heartbeat, ack, resolve, disconnect, and reconnect behavior.

## Scope

- Firmware upload verification.
- Serial COM port configuration.
- Real heartbeat test.
- Real LED state test.
- Real buzzer state test.
- Disconnect/reconnect behavior.
- Latency measurement.
- Hardware wiring/use instructions.

## Non-goals

- No medical device control.
- No treatment equipment.
- No wireless hospital device integration.
- No replacement of simulated adapter.
- No Sprint 11 interoperability work.

## Dependencies

- Sprint 4 firmware and serial adapter.
- Sprint 6 device validation baseline.
- Physical ESP32 hardware.
- USB cable and local serial access.

## Current Repository Assessment

- Firmware exists at `firmware/esp32_tracecare_alert/esp32_tracecare_alert.ino`.
- Device protocol documentation exists.
- Simulated adapter works.
- USB serial adapter has fake/mock tests.
- Real ESP32 has not been verified in the final Sprint 6 run.

## Proposed Architecture Changes

No core architecture changes unless real hardware testing exposes a bug.

Any changes must stay inside:

- device adapter,
- serial transport,
- firmware,
- device protocol docs.

API routes must not contain serial logic.

## Proposed Data Model Changes

No data model changes.

## Proposed API Changes

No required API changes.

Optional:

- Improve `GET /api/device/health` response only additively if needed.

## Proposed UI Changes

No major UI changes.

Allowed:

- clearer hardware connected/offline labels,
- clearer fallback state copy.

## Hardware Test Cases

- Startup heartbeat returns `PONG`.
- Normal state maps to green LED and buzzer off.
- Warning state maps to yellow LED and short beep.
- Critical state maps to red blinking LED and intermittent buzzer.
- Acknowledge turns buzzer off.
- Resolve returns state to normal when no unresolved event remains.
- USB disconnect activates backend fallback.
- Reconnect restores hardware state sync.

## Tasks

1. Confirm firmware compiles/uploads.
2. Record board type and Arduino/PlatformIO version.
3. Configure `DEVICE_ADAPTER_MODE=usb_serial`.
4. Configure `DEVICE_SERIAL_PORT` through env only.
5. Verify heartbeat.
6. Run demo analysis and observe LED/buzzer.
7. Acknowledge/resolve events and observe device changes.
8. Disconnect and reconnect USB.
9. Measure trigger latency.
10. Update device protocol and hardware docs.

## Expected Files

- `docs/ESP32_HARDWARE_VERIFICATION.md`
- Optional update to `docs/DEVICE_PROTOCOL.md`
- Optional update to firmware if real testing finds a protocol issue

## Migration Strategy

No migration.

## Testing Plan

- Existing backend device tests.
- Fake serial transport tests.
- Real hardware manual verification.
- Docker simulated mode regression.
- Frontend build.

## Acceptance Criteria

- Real ESP32 heartbeat works.
- Real LED and buzzer match backend state.
- Disconnect/reconnect behavior is documented and verified.
- Simulated mode remains available and unchanged.
- Hardware limitations are documented.

## Definition of Done

- Sprint status is `Completed` only if real hardware is tested.
- If no ESP32 is available, status remains `In Progress`.
- No claims are made that simulated tests verify real hardware.

## Deviations

TBD.

## Technical Decisions

TBD.

## Known Issues

TBD.

## Next Sprint Dependency

Sprint 12 release checklist should include whether hardware demo is enabled or skipped.

