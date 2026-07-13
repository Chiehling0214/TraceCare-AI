# Sprint 8: GCE Demo Deployment

## Status

In Progress

## Background

The prototype now runs through Docker Compose locally. A GCE deployment can provide a remote demo environment or backup path for judging. This sprint is deployment-oriented, not product-feature-oriented.

## Goal

Deploy the existing Docker Compose demo to Google Compute Engine with repeatable setup, health checks, demo reset, and teardown instructions.

## User Stories

- As a demo operator, I can deploy TraceCare AI to a GCE VM from documented steps.
- As a presenter, I can access the frontend remotely for backup demos.
- As a maintainer, I can tear down the VM and avoid unnecessary cloud costs.
- As a reviewer, I can verify that cloud deployment still uses only synthetic data.

## Scope

- GCE VM setup documentation.
- Docker and Docker Compose setup.
- `.env` template for GCE.
- Firewall/port guidance.
- Health checks.
- Demo reset/seed/run validation on GCE.
- Optional Ollama deployment decision matrix.
- Cost and teardown notes.

## Non-goals

- No production hospital deployment.
- No Kubernetes.
- No managed database.
- No real authentication/RBAC.
- No HTTPS automation unless explicitly needed for the demo.
- No real patient data.
- No external generative AI API.

## Dependencies

- Sprint 6 Docker Compose verification.
- Sprint 7 demo script and preflight checklist.

## Current Repository Assessment

- Docker Compose exists.
- Root `.env` controls host ports and backend/frontend settings.
- Backend uses SQLite in Docker named volume.
- Demo reset/seed/run endpoints exist.
- No GCE deployment documentation exists.

## Proposed Architecture Changes

No application architecture changes expected.

Deployment may add:

- GCE environment file example,
- deployment runbook,
- optional systemd or restart policy notes.

## Proposed Data Model Changes

No data model changes.

## Proposed API Changes

No API changes.

## Proposed UI Changes

No UI changes.

## Environment Variables

Document GCE values for:

- `BACKEND_HOST_PORT`
- `FRONTEND_HOST_PORT`
- `DATABASE_URL`
- `FRONTEND_ORIGIN`
- `VITE_API_BASE_URL`
- `SEED_ON_STARTUP`
- `LLM_MODE`
- `LOCAL_LLM_BASE_URL`
- `LOCAL_LLM_MODEL`
- `DEVICE_ADAPTER_MODE`
- `DEMO_MANAGEMENT_ENABLED`

## Tasks

1. Create `docs/GCE_DEPLOYMENT.md`.
2. Define recommended GCE VM specs:
   - app-only demo,
   - app plus CPU Ollama,
   - app plus GPU local model.
3. Document firewall rules.
4. Document Docker installation steps.
5. Document repository clone or artifact transfer.
6. Document `.env` setup.
7. Run `docker compose up --build -d` on GCE.
8. Verify frontend/backend access.
9. Verify reset/seed/run-demo.
10. Document teardown steps.

## Expected Files

- `docs/GCE_DEPLOYMENT.md`
- Optional `.env.gce.example` if useful
- Optional README deployment section update

## Migration Strategy

No migration.

## Testing Plan

- `docker compose config`
- `docker compose up --build -d`
- backend `/health`
- frontend page load
- reset demo
- seed demo
- run demo analysis
- patient list verification
- simulated device state verification

## Acceptance Criteria

- GCE deployment instructions are complete enough to reproduce.
- Frontend is reachable from the intended demo machine.
- Backend health returns 200.
- Demo reset/seed/run works on GCE.
- Teardown and cost-control steps are documented.
- If local model is not configured on GCE, deterministic fallback is documented and verified.

## Definition of Done

- GCE deployment is actually verified or status remains `In Progress`.
- All commands and observed results are documented.
- No production claims are made.
- No real data is used.

## Deviations

- A real GCE VM was not provisioned because the implementation environment has no `gcloud` CLI, configured Google Cloud project, credentials, or billing authority. Cloud-dependent Acceptance Criteria remain `NOT VERIFIED`.
- HTTPS and reverse proxy automation remain out of scope. The documented direct-port demo restricts ingress by presenter/judge source CIDR.
- Sprint 7 documentation exists at Git checkpoint `c93107a`, but `docs/SPRINT_07.md` still records its own status as `In Progress`; Sprint 8 does not rewrite that prior sprint's verification history.

## Technical Decisions

- Use `.env.gce.example` plus `docker-compose.gce.yml` instead of changing the locally verified base Compose behavior.
- Default GCE to `LLM_MODE=disabled` and deterministic fallback. Ollama CPU/GPU paths are optional decisions requiring separate Sprint 9 verification.
- Force `DEVICE_ADAPTER_MODE=simulated` on GCE because a cloud VM cannot control an ESP32 attached to the presenter's computer.
- Add container restart policies and health checks only in the GCE override.
- Expose frontend and backend directly for the bounded demo, but require source-CIDR firewall restrictions because authentication/RBAC is not implemented.

## Known Issues

- Real GCE creation, remote frontend/backend access, reset/seed/run, and fallback behavior are `NOT VERIFIED`.
- Direct HTTP has no transport encryption and is suitable only for synthetic competition data on a restricted firewall rule.
- Development demo-management endpoints are unauthenticated; they must not be exposed broadly.
- CPU Ollama latency and GPU quota/cost are not measured.
- The base frontend container runs Vite's development server; Sprint 8 preserves it for compatibility rather than claiming production-grade serving.

## Implemented

- Added `.env.gce.example` with cloud-safe app-only defaults and public-origin placeholders.
- Added `docker-compose.gce.yml` with restart policies, backend/frontend health checks, dependency health gating, and Linux host-gateway mapping for optional Ollama.
- Added `scripts/gce-smoke.sh` covering health, frontend load, reset, seed, deterministic analysis, patient fixture, and simulated device state.
- Added `docs/GCE_DEPLOYMENT.md` covering VM sizing, firewall rules, Docker install, deployment, smoke, model options, backup, recovery, cost control, and teardown.
- Added README and roadmap deployment references.

## Acceptance Results

- GCE deployment instructions are complete enough to reproduce: PASS by documentation review; real execution pending.
- Frontend is reachable from the intended demo machine: NOT VERIFIED.
- Backend health returns 200 on GCE: NOT VERIFIED.
- Demo reset/seed/run works on GCE: NOT VERIFIED.
- Teardown and cost-control steps are documented: PASS.
- Deterministic fallback is documented for app-only GCE: PASS; GCE execution NOT VERIFIED.

## Test Results

- Base `docker compose config`: PASS before implementation.
- `docker compose -f docker-compose.yml -f docker-compose.gce.yml --env-file .env.gce.example config`: PASS; GCE environment, health checks, restart policies, dependency health gate, ports, and host gateway resolved correctly.
- Backend regression tests: PASS, 55 tests in 7.70 seconds; two existing FastAPI `on_event` deprecation warnings.
- Frontend `npx tsc --noEmit`: PASS.
- Frontend `npm run build`: PASS; Vite transformed 58 modules and completed in 6.43 seconds.
- `git diff --check`: PASS.
- Smoke script API fields were checked against current health, patient-list, and device-state schemas: PASS.
- Native shell syntax execution: NOT VERIFIED because WSL bash startup was denied in the implementation environment; the script uses Bash strict mode and standard `curl`, `mktemp`, and Python 3 facilities available in the documented Ubuntu target.
- The first local Docker attempt was blocked because Docker Desktop was not running. After Docker Desktop started, `docker compose -f docker-compose.yml -f docker-compose.gce.yml up --build -d` passed and both containers became healthy.
- Local backend/frontend smoke: PASS; backend `/health` returned `ok` and frontend returned HTTP 200.
- Local synthetic demo workflow: PASS; reset, seed, and deterministic analysis produced 5 patients, P001 `HIGH_RISK`, P010 `REVIEW_REQUIRED`, and backend device state `CRITICAL` with the `simulated` adapter.
- Real GCE smoke: NOT VERIFIED because no cloud environment was available.

## Next Sprint Dependency

Sprint 9 local LLM verification may reuse GCE deployment only if the selected VM has enough resources.
