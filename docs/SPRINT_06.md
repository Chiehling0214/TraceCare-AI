# Sprint 6: Quantitative Validation, Deployment, and Demo Hardening

## Status

Planned

## Background

Sprint 6 is the stabilization and validation sprint. It should not add major new product functionality. It packages the demo, measures deterministic and AI-assisted behavior where available, and improves reliability.

## Goal

Create a fixed validation dataset, measure rule/event/summary/device metrics, improve end-to-end tests and offline UI states, finalize Docker Compose, and produce demo operation/fallback documentation.

## User Stories

- As a demo operator, I can reset and run the full demo reliably.
- As a reviewer, I can see honest validation metrics and known limitations.
- As a developer, I can run end-to-end tests before a demo.
- As a team member, I can recover from backend, frontend, model, or hardware failure during demo.

## Scope

- Fixed validation dataset.
- Numeric rule correctness metrics.
- Contradiction detection precision/recall/F1.
- Event state synchronization success rate.
- LED/buzzer trigger latency if Sprint 4 hardware is available.
- LLM numeric consistency, citation precision, evidence coverage, abstention rate if Sprint 3 is implemented.
- End-to-end tests.
- UI loading/empty/error/offline hardening.
- Docker Compose finalization.
- Demo reset script.
- Demo runbook and failure fallback procedures.

## Non-goals

- No major new product features.
- No new clinical rule families.
- No production deployment hardening beyond demo needs.
- No real patient data.

## Dependencies

- Sprint 1 for contradiction metrics.
- Sprint 2 for lifecycle synchronization metrics.
- Sprint 3 for LLM metrics, if implemented.
- Sprint 4 for hardware latency metrics, if hardware is available.
- Sprint 5 for validation dataset and reset/demo flow.

## Current Repository Assessment

- Current backend tests are unit/API-level pytest tests.
- No browser E2E tests exist.
- Docker Compose exists and avoids Windows bind mount issues by building images and using named volume.
- No validation dataset exists beyond seed constants.
- No metrics/reporting scripts exist.
- Frontend has basic loading/error/empty states but no comprehensive offline mode.

## Proposed Architecture Changes

- Add validation runner scripts outside core business logic.
- Add metrics report generation from fixed fixtures.
- Add E2E test harness.
- Keep demo hardening separate from application feature code where possible.

## Proposed Data Model Changes

No required core data model changes.

Optional:

- validation run records,
- metric result JSON files,
- demo run logs.

Prefer file-based reports for Sprint 6 unless persistence is clearly needed.

## Proposed API Changes

No major product API required.

Possible development-only endpoints:

- `GET /api/development/demo-status`
- `POST /api/development/reset-demo`

If Sprint 5 already provides these, do not duplicate.

## Proposed UI Changes

- Improve offline banner when backend is unavailable.
- Improve loading and retry states.
- Add demo status panel if useful.
- Ensure graph/summary/device panels degrade gracefully when dependencies are unavailable.

## Synthetic Test Data

- Fixed validation fixture covering:
  - rapid lab trigger,
  - stable labs,
  - insufficient labs,
  - contradiction positive,
  - contradiction negative,
  - duplicate prevention,
  - deferred/acknowledged/resolved lifecycle,
  - evidence package complete/incomplete cases,
  - hardware/simulated device states.

## Tasks

1. Define validation dataset and expected outputs.
2. Add metric calculation scripts.
3. Add E2E tests for main demo flow.
4. Add UI offline/retry improvements.
5. Verify Docker Compose from clean state.
6. Add demo reset script.
7. Add demo runbook.
8. Add fallback procedures for backend, frontend, local LLM, and ESP32 failure.
9. Generate final limitations report.

## Expected Files

- validation fixtures.
- validation runner scripts.
- E2E test files.
- demo reset/run scripts.
- demo runbook documentation.
- metrics output documentation.

## Migration Strategy

- No schema migration should be needed.
- If validation run persistence is added, it must be additive and optional.
- Demo reset must be explicit and development-only.

## Testing Plan

- Run backend tests.
- Run frontend build.
- Run E2E demo test.
- Run validation metrics script.
- Run Docker Compose from clean build.
- Verify no real patient data is included.

## Acceptance Criteria

- Fixed validation dataset produces documented expected metrics.
- E2E tests cover seed, analysis, patient detail, evidence, acknowledge, resolve, and device state.
- Docker Compose starts frontend/backend from clean checkout.
- Demo reset works.
- Runbook documents normal flow and failure fallback.
- Unimplemented metrics are explicitly marked not applicable or blocked.

## Risks and Mitigations

- Risk: metrics reveal weak performance.
  - Mitigation: report honestly and scope as prototype.
- Risk: Docker/platform issues consume sprint time.
  - Mitigation: freeze feature work and focus on reproducible setup.
- Risk: hardware/model dependencies are unavailable.
  - Mitigation: simulated and deterministic fallback metrics remain valid.

## Definition of Done

- Demo can be reset and run repeatably.
- Metrics are generated from fixed data.
- E2E tests cover the main story.
- Known limitations are documented.
- No new major feature work is introduced.

## Next Sprint Dependency

No Sprint 7 is planned in this roadmap. Any future work must be separately scoped after Sprint 6 validation results.
