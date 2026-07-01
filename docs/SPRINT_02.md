# Sprint 2: Risk Fusion and Event Lifecycle

## Status

Planned

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

## Proposed Data Model Changes

TBD after Sprint 1 implementation for final event/evidence identifiers.

Likely additive structures:

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

Avoid destructive changes to Sprint 0 tables unless a migration is explicitly documented.

## Proposed API Changes

Add:

- `POST /api/events/{event_id}/defer`
- `GET /api/events/{event_id}/actions`
- `GET /api/patients/{patient_id}/risk`
- `POST /api/prototype/run-risk-evaluation`

Extend:

- `GET /api/patients` with risk reason fields if backward-compatible.
- `GET /api/events/{event_id}` with lifecycle action history if practical.
- `GET /api/device-state` to reflect unified risk priority.

## Proposed UI Changes

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

## Next Sprint Dependency

Sprint 3 depends on Sprint 2 only for stable evidence/risk context. LLM summaries must cite evidence and must not calculate risk; the risk result should come from Sprint 2 deterministic services.
