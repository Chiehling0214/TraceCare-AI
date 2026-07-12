# Sprint 9: Local LLM Verification and Summary Quality

## Status

Planned

## Background

Sprint 3 introduced evidence-first summaries, local-only LLM adapter support, deterministic fallback, and post-generation validation. Sprint 6 measured fallback validation behavior but did not verify a real local model during the final validation run.

Sprint 9 focuses on real local LLM verification and summary quality without weakening deterministic safety checks.

## Goal

Verify at least one local Ollama model end-to-end, improve prompt reliability, measure summary validation behavior, and document model-specific limitations.

## User Stories

- As a presenter, I can show local-only generated summaries if the model is available.
- As a reviewer, I can see when the app used a real local model versus deterministic fallback.
- As a developer, I can evaluate model output quality with fixed synthetic evidence cases.
- As a safety reviewer, I can confirm invalid summaries still reject or fall back.

## Scope

- Local Ollama availability preflight.
- Fixed summary evaluation cases.
- Prompt tuning within evidence-first constraints.
- Model-specific validation metrics.
- Rejection/fallback demonstration.
- Documentation for expected local model behavior.

## Non-goals

- No external AI APIs.
- No cloud LLM APIs.
- No diagnosis.
- No treatment advice.
- No autonomous risk calculation by LLM.
- No vector database unless separately scoped.
- No model fine-tuning.

## Dependencies

- Sprint 3 summary adapter and validator.
- Sprint 6 validation runner.
- Local Ollama runtime and model availability.

## Current Repository Assessment

- `LLM_MODE=ollama` is configurable.
- Ollama adapter exists.
- Deterministic fallback exists.
- Summary validator rejects unsupported citations, numeric mismatches, and banned language.
- Prompt may still produce rejected outputs depending on local model behavior.

## Proposed Architecture Changes

Keep layers separated:

- Evidence Package builder.
- LLM adapter.
- Prompt/template generation.
- Post-generation validator.
- Summary persistence.

No API route should contain summary business logic.

## Proposed Data Model Changes

No required data model changes.

Optional:

- Add model evaluation report files under docs.

## Proposed API Changes

No required API changes.

Optional development-only endpoint if useful:

- `GET /api/development/llm-health`

Only add if it materially improves demo preflight.

## Proposed UI Changes

- Show clearer local model unavailable/fallback messaging if needed.
- Do not hide validation failures.
- Do not present generated summaries as clinical advice.

## Synthetic Test Data

Use fixed synthetic patients and evidence packages from Sprint 6.

Required cases:

- sufficient patient summary,
- sufficient handoff summary,
- insufficient evidence abstention,
- numeric mismatch rejection,
- unknown citation rejection,
- unsupported contradiction claim rejection,
- local model unavailable fallback.

## Tasks

1. Define local LLM evaluation cases.
2. Add local LLM preflight command/documentation.
3. Verify Ollama `/api/tags`.
4. Verify at least one configured local model.
5. Tune prompt if output fails due to preventable formatting issues.
6. Run generated summary validation metrics.
7. Document generated/fallback/abstained/rejected rates.
8. Keep deterministic fallback tests passing.

## Expected Files

- `docs/LOCAL_LLM_EVALUATION.md`
- Optional backend tests for prompt/adapter behavior
- Optional validation fixture additions
- Optional README local model section update

## Migration Strategy

No migration.

## Testing Plan

- Backend summary tests.
- Local Ollama health check.
- At least one real local inference, if model available.
- Fake adapter rejection tests.
- Deterministic fallback tests.
- Frontend build.
- Docker fallback verification if Ollama unavailable from container.

## Acceptance Criteria

- At least one local model is actually verified, or Sprint remains `In Progress`.
- Every returned generated sentence cites valid evidence IDs.
- Numeric mismatch still rejects or falls back.
- Unsupported claims still reject or fall back.
- Model unavailable path remains deterministic and user-visible.
- No external AI API is called.

## Definition of Done

- Local model verification results are documented.
- Summary quality metrics are documented.
- Safety validator remains strict.
- Sprint status is `Completed` only if real local inference is verified.

## Deviations

TBD.

## Technical Decisions

TBD.

## Known Issues

TBD.

## Next Sprint Dependency

If Sprint 10 hardware verification is demoed together with local LLM, presenter scripts should include fallback timing for both dependencies.

