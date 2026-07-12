# Sprint 11: Synthetic Interoperability Adapter

## Status

Planned

## Background

TraceCare AI currently imports fixed-schema synthetic CSV and JSON files. Competition reviewers may ask how the prototype could connect to hospital systems in the future. Sprint 11 demonstrates integration potential using synthetic-only, fixed-schema interoperability data without connecting to real HIS/LIS/EMR or FHIR servers.

## Goal

Add a synthetic-only interoperability adapter that maps fixed external-style JSON into existing TraceCare patient, lab, document, and fact models while preserving validation, source tracking, and idempotency.

## User Stories

- As a reviewer, I can see how structured external data could map into TraceCare.
- As a developer, I can validate synthetic interoperability fixtures before commit.
- As a safety reviewer, I can confirm non-synthetic identifiers are rejected.
- As a demo operator, I can run interoperability import repeatedly without duplicates.

## Scope

- Synthetic external-style JSON schema.
- Mapping documentation.
- Preview and commit flow, reusing Sprint 5 patterns.
- Validation errors for unsupported fields, invalid types, invalid times, invalid units, and non-synthetic identifiers.
- Source metadata preservation.
- Idempotent imports.

## Non-goals

- No real FHIR server.
- No real HIS/LIS/EMR connection.
- No OAuth.
- No real patient data.
- No arbitrary PDF/Word parsing.
- No full FHIR compliance.
- No production interoperability certification.

## Dependencies

- Sprint 5 import service.
- Sprint 1 document/fact model.
- Sprint 0 patient/lab model.
- Sprint 6 validation workflow.

## Current Repository Assessment

- CSV lab import exists.
- JSON clinical document import exists.
- Import metadata table exists.
- Demo reset/seed/run exists.
- No interoperability-shaped fixture exists.

## Proposed Architecture Changes

Add a service layer adapter:

- parser,
- validator,
- mapper,
- deduplicator,
- persistence coordinator.

Do not put mapping logic directly in API routes.

## Proposed Data Model Changes

Prefer no schema change.

If additional import kind tracking is required, reuse existing `ImportBatch.import_kind`.

## Proposed API Changes

Optional endpoints:

```http
POST /api/import/interoperability/preview
POST /api/import/interoperability/commit
```

Only add these if Sprint 11 is implemented.

## Proposed UI Changes

Optional Demo Data page section:

- synthetic interoperability JSON input,
- preview,
- commit,
- validation errors.

Must clearly state synthetic-only and non-production.

## Synthetic Test Data

Fixed JSON cases:

- valid external-style lab and document bundle,
- missing required patient code,
- non-synthetic patient identifier,
- invalid unit,
- invalid timestamp,
- duplicate bundle,
- unsupported resource type,
- mixed valid/invalid bundle rollback.

## Tasks

1. Define schema.
2. Document mapping to internal models.
3. Add validation service.
4. Add preview/commit endpoints.
5. Add UI section if needed.
6. Add tests for validation, rollback, and idempotency.
7. Add demo fixture.
8. Update docs.

## Expected Files

- `docs/SYNTHETIC_INTEROPERABILITY.md`
- backend interoperability schema/service/tests
- optional frontend import section
- synthetic fixture file

## Migration Strategy

No migration unless existing import metadata cannot represent the new import kind.

## Testing Plan

- Valid import preview.
- Valid import commit.
- Invalid identifier rejection.
- Invalid unit/time rejection.
- Duplicate import idempotency.
- Transaction rollback.
- Existing Sprint 0-6 regression tests.
- Frontend type check/build if UI changes.

## Acceptance Criteria

- Only fixed synthetic schema is accepted.
- Non-synthetic identifiers are rejected.
- Duplicate imports do not create duplicate records.
- Source metadata is preserved.
- Existing Sprint 0-6 flows remain compatible.

## Definition of Done

- Adapter is documented.
- Tests pass.
- Demo fixture is synthetic.
- No claim of real FHIR/HIS/LIS/EMR integration is made.

## Deviations

TBD.

## Technical Decisions

TBD.

## Known Issues

TBD.

## Next Sprint Dependency

Sprint 12 release checklist should mention that Sprint 11 is synthetic interoperability only.

