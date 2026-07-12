# Sprint 7: Competition Demo Polish and Judge Package

## Status

In Progress

## Background

Sprint 0 through Sprint 6 completed the core TraceCare AI prototype: synthetic data, deterministic rules, evidence graph, lifecycle, local-only summaries, simulated/serial device adapters, import/demo management, validation metrics, Docker smoke verification, and demo runbook.

Sprint 7 should not add major product functionality. Its purpose is to make the project easier to present, judge, reset, and explain under competition conditions.

## Goal

Create a polished competition demo package with presenter scripts, judge-facing Q&A, preflight checks, screenshots/state expectations, and final safety framing.

## User Stories

- As a presenter, I can run a 3-minute, 5-minute, or 10-minute demo without reading code.
- As a judge, I can clearly understand what is deterministic, what is local-only AI, and what is simulated hardware.
- As a demo operator, I can run a preflight checklist and know whether the system is ready.
- As a team member, I can explain limitations honestly without weakening the demo story.

## Scope

- Demo scripts for 3-minute, 5-minute, and 10-minute presentations.
- Judge-facing Q&A document.
- Demo preflight checklist.
- Expected UI state checklist.
- Failure fallback checklist for Docker, backend, frontend, Ollama, and ESP32.
- Competition-safe wording review.
- Optional small UI copy polish if it improves clarity.

## Non-goals

- No new backend business logic.
- No new clinical rules.
- No new database schema.
- No new AI model integration.
- No Sprint 8 deployment work.
- No real patient data.
- No diagnosis or treatment recommendation features.

## Dependencies

- Sprint 6 Docker and validation workflow.
- Sprint 5 reset/seed/run-demo workflow.
- Sprint 3 summary fallback behavior.
- Sprint 4 simulated device mode.

## Current Repository Assessment

- `docs/DEMO_RUNBOOK.md` exists.
- `docs/SPRINT_06_VALIDATION_RESULTS.md` exists.
- Docker demo runs on root `.env` ports `8001` and `5176`.
- No dedicated competition script or judge Q&A file exists.
- No release checklist exists.

## Proposed Architecture Changes

No architecture changes expected.

## Proposed Data Model Changes

No data model changes.

## Proposed API Changes

No API changes.

## Proposed UI Changes

Only small text or label refinements are allowed if they clarify:

- synthetic-only data,
- prototype/non-medical status,
- deterministic rule behavior,
- local-only summary behavior,
- simulated device fallback.

No redesign.

## Tasks

1. Create `docs/DEMO_SCRIPT.md`.
2. Create `docs/JUDGE_QA.md`.
3. Create `docs/RELEASE_CHECKLIST.md`.
4. Add a concise demo preflight checklist.
5. Add expected UI state checklist for the main demo flow.
6. Document how to recover from Docker/backend/frontend/Ollama/ESP32 failure during presentation.
7. Review visible UI text for competition clarity.
8. Run Docker demo smoke after documentation is complete.

## Expected Files

- `docs/DEMO_SCRIPT.md`
- `docs/JUDGE_QA.md`
- `docs/RELEASE_CHECKLIST.md`
- Optional small updates to `README.md`, `docs/DEMO_RUNBOOK.md`, or `docs/UI_REFERENCE.md`

## Migration Strategy

No migration.

## Testing Plan

- Run `docker compose up --build -d`.
- Verify backend health.
- Verify frontend loads.
- Run reset/seed/run-demo.
- Walk through P001 detail.
- Generate deterministic fallback summary.
- Confirm simulated device state.
- Confirm documentation matches observed behavior.

## Acceptance Criteria

- Presenter can follow the demo script without reading source code.
- Judge Q&A clearly explains deterministic rules, local-only AI, evidence citations, and limitations.
- Preflight checklist catches missing Docker/backend/frontend service states.
- Demo fallback procedures are documented.
- No product behavior is changed except optional copy polish.

## Definition of Done

- Demo script exists.
- Judge Q&A exists.
- Release/preflight checklist exists.
- Docker demo smoke passes after documentation updates.
- Sprint 7 status is set to `Completed` only after documentation and smoke verification pass.

## Deviations

- No UI copy was changed because the existing visible prototype, synthetic-data, local-only summary, and non-medical device labels already satisfy the competition clarity requirement.
- Backend regression execution is subject to the existing Windows pytest process-exit issue; Docker smoke and observed test completion are recorded separately.

## Technical Decisions

- Sprint 7 is documentation-only and introduces no backend, frontend, API, schema, rule, LLM, or device behavior changes.
- The release checklist defaults competition reliability to simulated device mode; real ESP32 mode requires a separate passing hardware preflight.
- Ollama is treated as optional. Deterministic rules and fallback remain the primary guaranteed demo path.

## Known Issues

- Real ESP32 behavior must be verified on the presentation machine before it is described as live hardware.
- Real local-LLM output can vary and may be rejected by validation; the presenter must be ready to show deterministic fallback.
- Sprint 6 and Sprint 7 changes are currently uncommitted on top of the Sprint 5 Git checkpoint.

## Next Sprint Dependency

Sprint 8 can use Sprint 7 documentation as the baseline for GCE deployment validation.
