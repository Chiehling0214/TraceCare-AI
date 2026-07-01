# Sprint 4: ESP32 and Physical Alerting

## Status

Planned

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
- No firmware directory exists.
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

## Next Sprint Dependency

Sprint 6 depends on Sprint 4 for hardware latency and synchronization metrics. If Sprint 4 hardware is not available, Sprint 6 must mark hardware metrics as simulated-only.
