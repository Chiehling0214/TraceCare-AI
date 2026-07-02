# Sprint 2: Risk Fusion and Event Lifecycle

## Status

Completed

## Background

Sprint 0 supports one event type, `RAPID_LAB_CHANGE`, with a simple lifecycle. Sprint 1 is planned to add `CONTRADICTION` events and evidence graph support. Sprint 2 should combine these event types into a deterministic risk model and make the event lifecycle more realistic for a demo without adding diagnosis or treatment recommendations.

## Goal

Create a unified deterministic risk service and richer event lifecycle that supports `REVIEW_REQUIRED`, `HIGH_RISK`, timeout handling, acknowledge, defer, resolve, action history, and audit trail.

## User Stories

- As a reviewer, I can see why a patient is ranked as normal, review-required, or high-risk.
- As a reviewer, I can defer an event with a reason while keeping it visible.
- As a demo operator, I can show that unacknowledged events age and may escalate deterministically.
- As an auditor, I can see who or what action changed event state in the prototype.
- As a developer, I can test risk calculations without invoking an LLM.

## Scope

- Add deterministic risk fusion across Sprint 0 `RAPID_LAB_CHANGE` and Sprint 1 `CONTRADICTION`.
- Add event timeout rules for unacknowledged events.
- Add `defer` lifecycle action.
- Add action/audit event recording.
- Update patient sorting by risk, unresolved event age, and unresolved event count.
- Update frontend event UI to show lifecycle actions and history.
- Preserve Sprint 0 acknowledge/resolve APIs or provide backward-compatible wrappers.

## Non-goals

- No LLM-calculated risk.
- No diagnosis.
- No treatment recommendation.
- No production alert policy.
- No authentication/authorization unless represented as synthetic actor labels.
- No real clinical escalation rules.

## Dependencies

- Sprint 0 event model and lifecycle.
- Sprint 1 `CONTRADICTION` event support.
- Sprint 1 evidence identifiers for facts/documents/events.

## Current Repository Assessment

- Current `patient_service.patient_summary` derives current severity directly from unresolved events.
- Existing event statuses are `OPEN`, `ACKNOWLEDGED`, and `RESOLVED`.
- Existing event API supports acknowledge and resolve only.
- No action/audit table exists.
- No actor/user model exists.
- Device state currently reads unresolved `ClinicalEvent` rows directly.

## Proposed Architecture Changes

- Add a deterministic risk service that consumes unresolved clinical events and returns patient-level risk.
- Add lifecycle service logic for `defer` and timeout evaluation.
- Add an action/audit recording boundary called Action Event or equivalent.
- Update device state service to consume unified risk/lifecycle output rather than duplicating event priority logic.
- Keep Sprint 0 endpoints backward-compatible.

## Implemented Data Model Changes

Sprint 2 uses additive schema changes only.

- Action/audit record:
  - event id
  - patient id
  - action type: `ACKNOWLEDGE`, `DEFER`, `RESOLVE`, `AUTO_ESCALATE`
  - actor label: synthetic user or system
  - note/reason
  - created time
- Event lifecycle additions:
  - deferred time
  - defer-until time
  - escalation reason or computed risk reason

Implementation:

- Added `event_actions`.
- Added nullable `clinical_events.deferred_at`.
- Added nullable `clinical_events.deferred_until`.
- Added nullable `clinical_events.escalated_at`.
- Added nullable `clinical_events.escalation_reason`.
- Existing `OPEN`, `ACKNOWLEDGED`, and `RESOLVED` statuses remain valid.
- Added `DEFERRED` for unresolved lifecycle state.
- SQLite demo initialization uses SQLAlchemy `create_all` plus an additive startup migration helper for the new nullable event columns.

## Implemented API Changes

Add:

- `POST /api/events/{event_id}/defer`
- `GET /api/events/{event_id}/actions`
- `GET /api/patients/{patient_id}/risk`
- `POST /api/prototype/run-risk-evaluation`

Extend:

- `GET /api/patients` with risk reason fields if backward-compatible.
- `GET /api/events/{event_id}` with lifecycle action history if practical.
- `GET /api/device-state` to reflect unified risk priority.

## Implemented UI Changes

- Patient overview shows risk reason summary.
- Patient overview sorting includes risk priority, oldest unresolved event, and unresolved event count.
- Patient detail shows event timeline/action history.
- Event cards show defer action where allowed.
- Device state panel indicates which event(s) drove the current state.

## Synthetic Test Data

- P001: rapid lab change plus contradiction event to test multiple event risk fusion.
- P002: stable labs and no contradiction.
- P003: insufficient data and no contradiction.
- Additional synthetic event aging data for timeout escalation.

## Tasks

1. Define deterministic risk rules and thresholds.
2. Add action/audit persistence.
3. Add defer lifecycle transition.
4. Add timeout evaluation logic.
5. Update patient summary sorting logic.
6. Update device state derivation to use risk/lifecycle service.
7. Add API routes for risk, defer, and actions.
8. Add frontend action history and defer controls.
9. Add tests for risk fusion, timeout, defer, action history, and existing Sprint 0 compatibility.

## Expected Files

- `backend/app/services/risk_service.py` or equivalent.
- `backend/app/services/lifecycle_service.py` or equivalent.
- new backend schema/model files for action/audit records.
- frontend API/type/component files for risk and event actions.
- backend tests for Sprint 2 lifecycle and risk.
- documentation updates after implementation.

## Migration Strategy

- Additive schema only.
- Preserve existing `acknowledge` and `resolve` behavior.
- If new statuses are added, document how `OPEN`, `ACKNOWLEDGED`, and `RESOLVED` map for existing API clients.
- Provide reset guidance for local SQLite demo if required.

## Testing Plan

- Existing Sprint 0 and Sprint 1 tests remain passing.
- Risk service returns deterministic patient risk for known synthetic scenarios.
- Deferred events remain unresolved and visible.
- Timeout rules escalate only under documented conditions.
- Action history records acknowledge, defer, resolve, and auto-escalate.
- Device state follows unified risk priority.

## Acceptance Criteria

- Patient risk is deterministic and explainable.
- Multiple event types can influence patient ranking.
- Defer, acknowledge, and resolve are testable end to end.
- Action history is visible through API and UI.
- No LLM or clinical diagnosis language is introduced.

## Risks and Mitigations

- Risk: lifecycle grows too complex.
  - Mitigation: implement only acknowledge, defer, resolve, and timeout.
- Risk: risk score appears clinical.
  - Mitigation: label as prototype risk state and show rule reasons.
- Risk: device state logic diverges from dashboard risk.
  - Mitigation: centralize risk/lifecycle derivation.

## Definition of Done

- Unified risk service exists and is covered by tests.
- Event lifecycle actions are persisted.
- UI shows action history and supports defer.
- Existing Sprint 0 and Sprint 1 flows still work.

## Implementation Summary

- Added deterministic risk service for unresolved `RAPID_LAB_CHANGE` and `CONTRADICTION` events.
- Added lifecycle service for acknowledge, defer, resolve, and timeout auto-escalation.
- Added persisted action history for `ACKNOWLEDGE`, `DEFER`, `RESOLVE`, and `AUTO_ESCALATE`.
- Updated patient summaries and ordering to use risk state, oldest unresolved event age, and unresolved event count.
- Updated simulated device state to derive priority from the unified risk/lifecycle service.
- Updated frontend to run lab analysis, contradiction analysis, and risk evaluation from the demo action.
- Updated frontend event cards to show lifecycle timestamps, escalation reason, action history, and defer controls.

## Deterministic Risk Rules

- `NORMAL`: no unresolved events.
- `REVIEW_REQUIRED`: unresolved prototype event exists but no high-risk driver is present.
- `HIGH_RISK`: any unresolved event is already `HIGH_RISK`, an `OPEN` event is at least 2 hours old, or multiple unresolved event types are present for the same synthetic patient.
- Unresolved statuses are `OPEN`, `ACKNOWLEDGED`, and `DEFERRED`.
- Deferred and acknowledged events remain visible until resolved.

## Acceptance Criteria Results

- Patient risk is deterministic and explainable: Passed.
- Multiple event types can influence patient ranking: Passed.
- Defer, acknowledge, and resolve are testable end to end: Passed.
- Action history is visible through API and UI: Passed.
- No LLM or clinical diagnosis language is introduced: Passed.

## Test Results

- Backend test suite: `26 passed`.
- Sprint 0 and Sprint 1 regression coverage remains in the same backend suite.
- Sprint 2 backend tests cover schema additions, risk fusion, defer, action history, timeout escalation, and invalid lifecycle paths.
- Frontend type check: passed.
- Frontend production build: passed.

## Deviations

- `GET /api/events/{event_id}` includes action history directly in `action_history`; `GET /api/events/{event_id}/actions` is also available for explicit audit retrieval.
- `POST /api/events/{event_id}/defer` accepts an optional reason and optional `defer_until`. If `defer_until` is omitted, the backend uses a deterministic default of four hours from the action time.
- Timeout auto-escalation is explicit through `POST /api/prototype/run-risk-evaluation`; ordinary reads calculate risk but do not mutate event severity.

## Technical Decisions

- Business logic lives in `risk_service` and `lifecycle_service`; API routes only orchestrate request/response handling.
- Time-dependent tests pass fixed `evaluated_at` values to avoid reliance on uncontrolled system time.
- Action history is intentionally stored with synthetic actor labels instead of a user table because formal authentication and authorization are out of scope.
- SQLite additive migration is limited to Sprint 2 nullable event columns because the prototype still uses SQLAlchemy `create_all` rather than Alembic.

## Known Issues

- The project still uses prototype SQLite initialization, not a production migration framework.
- No role-based permissions exist for lifecycle actions.
- Risk states are deterministic prototype review states only and are not clinical risk scores.

## Next Sprint Dependency

Sprint 3 depends on Sprint 2 only for stable evidence/risk context. LLM summaries must cite evidence and must not calculate risk; the risk result should come from Sprint 2 deterministic services.
