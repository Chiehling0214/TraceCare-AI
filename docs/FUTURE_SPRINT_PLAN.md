# TraceCare AI Future Sprint Plan

Status: Proposed

This document starts after Sprint 6. It is a planning document only; none of these sprints are implemented by this file.

TraceCare AI remains a synthetic-data prototype. Future work must not introduce real patient data, autonomous diagnosis, treatment recommendations, external generative AI APIs, or control of real medical/treatment devices unless a separately approved safety and compliance plan exists.

## Planning Assumptions

- Sprint 0 through Sprint 6 are the completed demo foundation.
- Current strongest demo path is Docker Compose with synthetic seed/reset/run-demo workflow.
- Local LLM remains optional and local-only.
- ESP32 remains optional; simulated adapter must stay available.
- GCE deployment is useful for demo hosting, but medical-production deployment is out of scope.

## Recommended Sprint Order

1. Sprint 7: Competition Demo Polish and Judge Package
2. Sprint 8: GCE Demo Deployment
3. Sprint 9: Local LLM Verification and Summary Quality
4. Sprint 10: ESP32 Hardware Verification
5. Sprint 11: Synthetic Interoperability Adapter
6. Sprint 12: Observability, QA Freeze, and Release Candidate

---

# Sprint 7: Competition Demo Polish and Judge Package

## Goal

Turn the completed prototype into a smooth, repeatable competition presentation.

## Scope

- Demo script for 3-minute, 5-minute, and 10-minute versions.
- Judge-facing feature checklist.
- Screenshots and expected UI states.
- Demo reset preflight checklist.
- Known limitations slide content.
- Better empty/loading/error copy where needed.
- Small UI copy polish only.

## Non-goals

- No new backend business logic.
- No new clinical rules.
- No new data model.
- No new AI model integration.

## Tasks

- Create `docs/DEMO_SCRIPT.md`.
- Create `docs/JUDGE_QA.md`.
- Add a demo preflight command checklist.
- Verify Docker demo from a clean reset.
- Polish UI wording where it improves demo clarity.
- Record known fallback paths: Docker fail, Ollama fail, ESP32 fail.

## Acceptance Criteria

- A presenter can run the demo from documentation without reading code.
- A judge can understand what is deterministic, what is local LLM, and what is simulated.
- Demo reset/run path works from Docker.
- No new product scope is introduced.

## Status Recommendation

Do this next. It has the best competition value and lowest technical risk.

---

# Sprint 8: GCE Demo Deployment

## Goal

Deploy the existing Docker Compose demo to a Google Compute Engine VM for remote judging or backup demo use.

## Scope

- GCE VM setup documentation.
- Docker and Docker Compose deployment steps.
- Environment variable template for GCE.
- Reverse proxy or direct port access decision.
- Basic health check and restart procedure.
- Optional Ollama deployment decision for CPU-only or GPU VM.

## Non-goals

- No production-grade hospital deployment.
- No real patient data.
- No formal auth/RBAC.
- No managed database migration.
- No Kubernetes.

## Tasks

- Create `docs/GCE_DEPLOYMENT.md`.
- Define recommended VM specs for:
  - app-only demo,
  - app plus Ollama CPU demo,
  - app plus GPU local model demo.
- Document firewall ports.
- Document `.env` for cloud.
- Verify `docker compose up --build -d` on GCE.
- Add backup/restore notes for the named Docker volume.

## Acceptance Criteria

- App is reachable from a browser.
- Backend health endpoint returns 200.
- Demo reset/seed/run-analysis works on GCE.
- If Ollama is unavailable, deterministic fallback still works.
- Deployment documentation includes teardown steps to avoid cost surprises.

## Status Recommendation

Do after Sprint 7 if remote demo reliability matters.

---

# Sprint 9: Local LLM Verification and Summary Quality

## Goal

Improve and verify local-only summary behavior without weakening evidence validation.

## Scope

- Verify one or more local Ollama models.
- Compare generated output against deterministic fallback.
- Improve prompts within the evidence-first constraints.
- Add summary quality rubric for traceability, clarity, citation coverage, and abstention.
- Keep deterministic fallback as mandatory.

## Non-goals

- No external AI API.
- No RAG/vector database unless separately scoped.
- No diagnosis/treatment recommendation.
- No model fine-tuning.

## Tasks

- Create fixed local LLM evaluation cases.
- Add model availability preflight check.
- Record pass/fail results per model.
- Tune prompt to reduce rejected outputs.
- Keep validator strict.
- Document expected failures and fallback behavior.

## Acceptance Criteria

- At least one local model is actually verified, or the sprint remains In Progress.
- Every generated sentence cites valid evidence IDs.
- Numeric mismatch and unsupported claims still reject or fall back.
- Fallback path works when Ollama is offline.

## Status Recommendation

Do only if local LLM is important to the final demo. Otherwise keep fallback-only.

---

# Sprint 10: ESP32 Hardware Verification

## Goal

Verify the physical alert device flow with real ESP32 hardware while preserving simulated mode.

## Scope

- Real serial connection verification.
- LED and buzzer behavior verification.
- Heartbeat, disconnect, reconnect, and fallback tests.
- Hardware demo checklist.
- Optional wiring diagram.

## Non-goals

- No medical device control.
- No treatment hardware.
- No networked hospital devices.
- No replacement of simulated adapter.

## Tasks

- Create hardware preflight checklist.
- Verify firmware upload.
- Verify serial protocol with backend.
- Measure LED/buzzer trigger latency.
- Document COM port configuration.
- Document fallback when hardware is absent.

## Acceptance Criteria

- Real ESP32 receives heartbeat.
- Real LED/buzzer state changes match backend device state.
- Disconnect/reconnect behavior is documented and tested.
- Simulated mode remains the default safe path.

## Status Recommendation

Do only when hardware is available. Otherwise keep as future scope.

---

# Sprint 11: Synthetic Interoperability Adapter

## Goal

Demonstrate how TraceCare could receive structured external data without connecting to real hospital systems.

## Scope

- Synthetic-only FHIR-like JSON adapter or import fixture.
- Mapping documentation from synthetic source fields to internal models.
- Validation and rejection of non-synthetic patient identifiers.
- Demo import path using existing Sprint 5 import architecture where possible.

## Non-goals

- No real FHIR server.
- No HIS/LIS/EMR connection.
- No real patient records.
- No arbitrary document parsing.

## Tasks

- Define synthetic interoperability fixture schema.
- Add validation-only import preview.
- Reuse existing patient/lab/document/fact persistence.
- Add tests for invalid identifiers and unsupported fields.
- Document mapping and limitations.

## Acceptance Criteria

- Adapter accepts only fixed synthetic schema.
- Imported data remains idempotent.
- Source metadata is preserved.
- Existing Sprint 0-6 workflows remain compatible.

## Status Recommendation

Useful if judges ask about integration potential, but lower priority than deployment/demo polish.

---

# Sprint 12: Observability, QA Freeze, and Release Candidate

## Goal

Freeze the project into a reliable final demo release.

## Scope

- Final regression checklist.
- Smoke test script.
- Versioned release notes.
- Basic structured logs for demo operations.
- Final limitations and future work summary.

## Non-goals

- No new features.
- No schema expansion unless required by a bug.
- No major UI redesign.

## Tasks

- Create `docs/RELEASE_CHECKLIST.md`.
- Add a minimal smoke command script if needed.
- Verify all docs match current behavior.
- Run full backend/frontend/Docker validation.
- Tag the release manually after user approval.

## Acceptance Criteria

- Clean checkout can run the demo by following docs.
- All known limitations are documented.
- No uncommitted release-critical changes remain.
- User explicitly approves any release tag or commit.

## Status Recommendation

Do last, after deciding whether Sprint 8-10 are needed.

---

## Suggested Immediate Next Step

Implement Sprint 7 next. It improves presentation quality without risking the stable Sprint 0-6 prototype.

Recommended Sprint 7 files:

- `docs/DEMO_SCRIPT.md`
- `docs/JUDGE_QA.md`
- `docs/RELEASE_CHECKLIST.md`

Recommended Sprint 7 verification:

- `docker compose up --build -d`
- backend health check
- frontend load check
- reset/seed/run-demo
- one patient detail walkthrough
- one summary fallback walkthrough
- one device fallback walkthrough

