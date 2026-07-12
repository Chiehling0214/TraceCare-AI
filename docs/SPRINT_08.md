# Sprint 8: GCE Demo Deployment

## Status

Planned

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

TBD.

## Technical Decisions

TBD.

## Known Issues

TBD.

## Next Sprint Dependency

Sprint 9 local LLM verification may reuse GCE deployment only if the selected VM has enough resources.

