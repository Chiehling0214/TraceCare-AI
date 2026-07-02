# Sprint 3: Evidence-first RAG and Local LLM

## Status

Completed

## Background

Sprint 0 proves deterministic lab event generation. Sprint 1 is planned to add documents, facts, contradiction detection, and evidence graph. Sprint 2 is planned to add deterministic risk fusion and lifecycle audit. Sprint 3 adds local-only summarization while preserving evidence-first behavior.

## Goal

Add a local LLM adapter and evidence package workflow that can generate patient and handoff summaries where each sentence maps to evidence IDs, numeric values are validated outside the model, and insufficient evidence results in abstention.

## User Stories

- As a reviewer, I can request a patient summary that cites the evidence it used.
- As a reviewer, I can see when the system refuses to summarize due to insufficient evidence.
- As a developer, I can run the app with LLM disabled and still get deterministic fallback output.
- As a demo operator, I can show local-only AI output without sending data to external APIs.

## Scope

- Add document index interface over existing structured synthetic documents/facts.
- Add evidence package builder from patient facts, labs, events, and graph evidence.
- Add local LLM adapter interface.
- Add configurable local model backend, TBD after environment validation.
- Add patient summary and handoff summary endpoints.
- Add citation completeness validation.
- Add numeric consistency validation.
- Add abstention behavior.
- Add deterministic fallback summary when LLM is disabled.

## Non-goals

- No external generative AI API.
- No LLM risk calculation.
- No LLM numeric calculation.
- No treatment advice.
- No arbitrary document parsing.
- No vector database unless a later local-only design explicitly requires it.

## Dependencies

- Sprint 1 evidence graph and source IDs.
- Sprint 2 deterministic risk output if included in summaries.
- Current local development/Docker setup.

## Current Repository Assessment

- No LLM/RAG code exists.
- No document/fact data exists until Sprint 1.
- No evidence package abstraction exists.
- Frontend currently displays deterministic data only.
- Docker images currently include Python and Node dependencies but no model runtime.

## Proposed Architecture Changes

- Add an `EvidencePackage` builder abstraction, not tied to a specific model.
- Add `LocalLLMAdapter` interface with a disabled/mock implementation.
- Keep model selection in configuration, not business logic.
- Add validators that run after generation and before returning text.
- Add deterministic fallback path available by configuration.

## Proposed Data Model Changes

TBD after Sprint 1 implementation.

Possible additions:

- Summary request/response audit records.
- Summary sentence citation mapping.
- Validation result records for numeric consistency, citation precision, and abstention reason.

## Proposed API Changes

Add:

- `POST /api/patients/{patient_id}/summaries/patient`
- `POST /api/patients/{patient_id}/summaries/handoff`
- `GET /api/summaries/{summary_id}`
- `GET /api/summaries/{summary_id}/evidence`

Responses must include:

- generated or fallback text,
- sentence-level evidence IDs,
- validation status,
- abstention reason when applicable,
- explicit local-only mode metadata.

## Proposed UI Changes

- Add summary panel to patient detail.
- Show generated summary with citation chips per sentence.
- Show validation status and abstention messages.
- Show deterministic fallback label when local LLM is disabled.
- Do not hide source evidence behind generated text.

## Synthetic Test Data

- P001 with lab event and contradiction event.
- P002 with stable/no-risk data.
- P003 with insufficient evidence to force abstention.
- A numeric mismatch fixture to verify validator rejection.

## Tasks

1. Define evidence package response shape.
2. Implement evidence package builder from existing APIs/models.
3. Add local LLM adapter interface and disabled implementation.
4. Add prompt/output contract for local summaries.
5. Add citation validation.
6. Add numeric consistency validation.
7. Add abstention rules.
8. Add summary APIs.
9. Add frontend summary panel.
10. Add tests for fallback, citation validation, numeric validation, and abstention.

## Expected Files

- backend evidence package service.
- backend local LLM adapter interface.
- backend summary service and schemas.
- frontend summary API/types/component.
- tests for summary validation.
- documentation of local model setup after model choice is validated.

## Migration Strategy

- Keep summary persistence optional for first implementation if API can be tested deterministically.
- If persistence is added, use additive tables only.
- Existing Sprint 0-2 APIs remain unchanged.

## Testing Plan

- Existing deterministic tests remain passing.
- LLM-disabled fallback returns deterministic summary.
- Generated summary with missing citation is rejected.
- Generated summary with numeric mismatch is rejected.
- Insufficient evidence returns abstention.
- No external network calls are made during tests.

## Acceptance Criteria

- Summary output is local-only or deterministic fallback.
- Every summary sentence maps to evidence IDs.
- Numeric values in summary match evidence package values.
- System abstains when evidence is insufficient.
- No risk level is calculated by the LLM.

## Risks and Mitigations

- Risk: local model is unavailable or slow.
  - Mitigation: keep disabled/fallback mode mandatory.
- Risk: citations are incomplete.
  - Mitigation: reject output unless every sentence cites evidence.
- Risk: users over-trust summaries.
  - Mitigation: show evidence and prototype warning beside summaries.

## Definition of Done

- Local LLM adapter boundary exists.
- Evidence package builder is tested.
- Summary endpoint returns validated cited output or abstention.
- Frontend displays citations and validation state.

## Implemented

- Added Evidence Package builder over existing synthetic patients, labs, documents, facts, events, and deterministic Sprint 2 risk output.
- Added local LLM adapter boundary with:
  - `disabled` mode,
  - deterministic fallback path,
  - fake/test adapter for automated validation tests,
  - optional Ollama local adapter interface.
- Added post-generation validators for:
  - missing sentence citations,
  - unknown evidence IDs,
  - numeric mismatch against cited evidence,
  - diagnosis/treatment language.
- Added summary persistence through additive `summary_records`.
- Added APIs:
  - `POST /api/patients/{patient_id}/summaries/patient`
  - `POST /api/patients/{patient_id}/summaries/handoff`
  - `GET /api/summaries/{summary_id}`
  - `GET /api/summaries/{summary_id}/evidence`
- Added frontend Evidence-first Summary panel on patient detail.
- Added Sprint 3 backend tests for evidence package shape, deterministic fallback, summary retrieval, abstention, generated-output validation fallback, and validator coverage for missing citations, unknown citations, numeric mismatches, uncited evidence mentions, and unsupported contradiction claims.

## Evidence Package Design

Evidence IDs use stable typed prefixes:

- `patient:{id}`
- `lab:{id}`
- `document:{id}`
- `fact:{id}`
- `event:{id}`
- `action:{id}`
- `risk:{patient_id}`

Each evidence item includes:

- ID
- type
- label
- text
- numeric values
- metadata

The package is snapshotted into `summary_records.evidence_package_json` so later retrieval can show exactly what was validated.

## LLM Adapter and Configuration

Environment variables:

```text
LLM_MODE=disabled
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=
LOCAL_LLM_TIMEOUT_SECONDS=120
```

Supported implementation modes:

- `disabled`: no model call; deterministic fallback is used.
- `fake-test`: automated tests only; not a real model integration.
- `ollama`: optional local-only adapter boundary using an Ollama-compatible local runtime.

No external generative AI API is used.

## Acceptance Results

- Summary output is local-only or deterministic fallback: PASS for deterministic fallback and verified local Ollama generation.
- Every summary sentence maps to evidence IDs: PASS.
- Numeric values in summary match evidence package values: PASS.
- System abstains when evidence is insufficient: PASS.
- No risk level is calculated by the LLM: PASS by architecture; risk evidence comes from Sprint 2 deterministic service.
- Real local model inference: PASS with local Ollama `llama3.2:3b` through Docker backend using `LOCAL_LLM_BASE_URL=http://host.docker.internal:11434`.

## Test Results

- Baseline backend test output before Sprint 3: `26 passed`.
- Sprint 3 backend test output: `9 passed`.
- Docker API smoke test produced `GENERATED` / `PASSED` patient and handoff summaries with local Ollama `llama3.2:3b`.
- Frontend type check: passed.
- Frontend production build: passed after the known sandbox `esbuild spawn EPERM` workaround.

## Deviations

- Summary persistence was implemented even though persistence was optional, because `GET /api/summaries/{summary_id}` and `GET /api/summaries/{summary_id}/evidence` require retrievable records.
- The first Sprint 3 implementation does not add a vector database. Existing structured evidence is sufficient for deterministic evidence package construction.
- The generated text is intentionally conservative. Sprint 3 prioritizes evidence traceability, local-only execution, validator safety, and deterministic fallback over rich clinical-style summarization.

## Technical Decisions

- LLM output is accepted only after validators pass. Invalid generated output is not returned to the UI; the service switches to deterministic fallback when fallback validation passes.
- Deterministic fallback avoids derived numeric aggregation so the numeric validator does not approve model-like calculations that are not explicitly present in cited evidence.
- P003 abstains because it lacks the minimum longitudinal synthetic evidence threshold: at least two labs and at least two synthetic documents.
- Summary services do not update clinical event status, risk state, or action history.

## Known Issues

- The optional Ollama adapter expects the local model to return strict JSON; model-specific prompt tuning may be needed later.
- Summary content is evidence-inventory oriented and intentionally sparse. A later sprint can improve readability by adding richer deterministic evidence facts without allowing the LLM to calculate risk, infer clinical meaning, or recommend treatment.
- The project still uses SQLAlchemy `create_all` plus additive prototype helpers rather than a formal migration framework.

## Next Sprint Dependency

Sprint 4 does not depend on Sprint 3. Sprint 6 validation depends on Sprint 3 if LLM metrics are included; otherwise those metrics must be marked not applicable.
