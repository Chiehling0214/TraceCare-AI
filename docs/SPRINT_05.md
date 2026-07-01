# Sprint 5: Data Import and Demo Data Management

## Status

Planned

## Background

Sprint 0 seed data is hard-coded in Python. Later sprints need richer synthetic datasets and repeatable demo setup. Sprint 5 adds fixed-schema import and demo reset flows without allowing real patient data or arbitrary document parsing.

## Goal

Support fixed-schema synthetic CSV lab import, fixed-schema JSON clinical document import, validation preview, import error reports, and one-command demo reset/seed/run flow.

## User Stories

- As a demo operator, I can reset the demo and seed all synthetic scenarios.
- As a developer, I can import fixed-schema lab CSV fixtures and see validation errors.
- As a developer, I can import fixed-schema synthetic clinical documents.
- As a reviewer, I can see source filenames and source positions after import.

## Scope

- Fixed-schema CSV lab import.
- Fixed-schema JSON clinical document import.
- Preview and validation result API.
- Error reporting for missing fields, invalid units, invalid times, duplicates.
- Preserve source filename and original position.
- Demo dataset for multiple synthetic patients.
- Reset/seed/run-demo workflow.

## Non-goals

- No real patient data.
- No FHIR.
- No arbitrary PDF/Word parsing.
- No free-form NLP document extraction.
- No production upload security model.

## Dependencies

- Sprint 0 lab model.
- Sprint 1 document/fact model.
- Sprint 2 lifecycle if imported data triggers demo events.

## Current Repository Assessment

- Seed data is Python constants in `backend/app/seed/synthetic.py`.
- No upload/import endpoint exists.
- No reset endpoint or script exists.
- Docker Compose uses named volume, so reset needs a container-safe path.
- Frontend has no upload page.

## Proposed Architecture Changes

- Add import validation service separate from persistence.
- Add import preview endpoint that does not commit data.
- Add import commit endpoint for validated synthetic data.
- Add demo reset service/script for local and Docker use.
- Keep import schemas fixed and versioned.

## Proposed Data Model Changes

TBD after Sprint 1 model implementation.

Possible additions:

- Import batch record.
- Import row error record.
- Source file metadata.

Avoid storing real patient identifiers; enforce synthetic patient codes.

## Proposed API Changes

Add:

- `POST /api/import/labs/preview`
- `POST /api/import/labs/commit`
- `POST /api/import/documents/preview`
- `POST /api/import/documents/commit`
- `GET /api/imports/{import_id}/errors`
- `POST /api/development/reset-demo`
- `POST /api/development/seed-demo`
- `POST /api/development/run-demo-analysis`

Development endpoints must be clearly marked as prototype/demo-only.

## Proposed UI Changes

- Add demo data management page or panel.
- Add synthetic data warning on import page.
- Add preview tables and validation error list.
- Add reset/seed/run-demo buttons.

## Synthetic Test Data

- Valid lab CSV.
- Invalid lab CSV with missing value, invalid unit, duplicate row, invalid timestamp.
- Valid document JSON matching Sprint 1 fixed format.
- Invalid document JSON with missing source position or unsupported fact type.
- Larger demo dataset with multiple synthetic patients.

## Tasks

1. Define CSV and JSON schemas.
2. Add validation service.
3. Add preview endpoints.
4. Add commit endpoints.
5. Add import error reporting.
6. Add demo reset/seed/run script or endpoint.
7. Add frontend import/demo management UI.
8. Add tests for valid/invalid imports and reset behavior.

## Expected Files

- backend import services and schemas.
- backend demo management service.
- synthetic fixture files under a demo data directory.
- frontend import/demo management components.
- tests for import validation and reset.
- documentation for file schemas.

## Migration Strategy

- Additive import metadata tables only if persistence is needed.
- Reset flow may delete synthetic demo records but must be explicit and development-only.
- Preserve Sprint 0 seed path for simple demos.

## Testing Plan

- Valid files preview and commit.
- Invalid files produce structured error reports.
- Duplicate rows are rejected or skipped with explicit report.
- Reset clears demo records and reseed recreates expected dataset.
- Existing event analysis works after import.

## Acceptance Criteria

- Fixed-schema imports work for synthetic data only.
- Invalid imports do not partially corrupt data.
- Source filenames and positions are preserved.
- Demo reset/seed/run flow is repeatable.
- Upload/import UI warns against real patient data.

## Risks and Mitigations

- Risk: import scope expands into generic ingestion.
  - Mitigation: fixed schema only.
- Risk: reset endpoint is unsafe.
  - Mitigation: development-only config and clear naming.
- Risk: imported data breaks demo determinism.
  - Mitigation: version fixtures and expected outcomes.

## Definition of Done

- Import preview/commit is tested.
- Demo reset/seed/run is documented.
- Synthetic warnings are visible.
- Existing demo flows still work.

## Next Sprint Dependency

Sprint 6 depends on Sprint 5 for fixed validation/demo datasets and reliable reset procedures.
