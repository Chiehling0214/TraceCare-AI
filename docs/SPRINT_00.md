# TraceCare AI Sprint 0

## Goal

Build a minimum end-to-end competition prototype that turns synthetic creatinine lab data into traceable clinical events, displays evidence, tracks acknowledgement/resolution, and reflects event status in a simulated device state.

## Scope

- Synthetic patients and creatinine lab results only.
- Deterministic prototype rule execution only.
- Local FastAPI backend with SQLite through `DATABASE_URL`.
- React/Vite frontend with patient overview and patient detail pages.
- Event acknowledgement and resolution workflow.
- Simulated device state adapter.
- Backend tests for seed, analysis, events, 404s, and device state.

## Non-goals

- No diagnosis or treatment advice.
- No real patient data.
- No LLM, RAG, embeddings, vector database, PDF parsing, FHIR, login, permissions, or document upload.
- No real ESP32 or USB serial communication.
- No production clinical rule set.

## Architecture

```text
frontend React/Vite
  -> REST API
backend FastAPI
  -> SQLAlchemy services
  -> SQLite database configured by DATABASE_URL
```

Core backend services:

- `seed.synthetic`: repeatable synthetic seed data.
- `rule_service`: deterministic `RAPID_INCREASE` prototype rule.
- `event_service`: event detail, acknowledgement, resolution.
- `device_service`: adapter interface with simulated implementation.

## Data Model

- `Patient`: synthetic patient identity.
- `LabResult`: creatinine values with source document and observation time.
- `ClinicalEvent`: rule-created event with severity/status lifecycle.
- `EvidenceLink`: relation between event and source lab records.

## Prototype Rule

Rule ID: `RAPID_INCREASE`

For one patient, if creatinine changes from `0.8 mg/dL` to `1.3 mg/dL` within `24` hours, create one `REVIEW_REQUIRED` `RAPID_LAB_CHANGE` event.

This is a synthetic demonstration rule only. It is not a validated clinical rule.

## API

- `GET /health`
- `GET /api/patients`
- `GET /api/patients/{patient_id}`
- `GET /api/patients/{patient_id}/labs`
- `GET /api/patients/{patient_id}/events`
- `GET /api/events/{event_id}`
- `POST /api/events/{event_id}/acknowledge`
- `POST /api/events/{event_id}/resolve`
- `POST /api/prototype/run-analysis`
- `GET /api/device-state`

## Acceptance Criteria

- Synthetic seed can be run repeatedly without duplicate patients or labs.
- P001 triggers one `RAPID_INCREASE` event.
- P002 does not trigger an event.
- P003 reports insufficient data.
- Re-running analysis skips the duplicate event.
- Event detail includes previous/current lab values, times, source documents, and evidence links.
- Acknowledgement changes device state from warning buzzer to acknowledged/off.
- Resolution returns the device state to normal when no unresolved events remain.
- Backend tests pass.

## Known Limitations

- SQLite is used for Sprint 0 local persistence.
- Device state is simulated and does not control hardware.
- Only creatinine is supported.
- Rule parameters are intentionally narrow for the demo dataset.
- Frontend is desktop-first and intentionally avoids charts, evidence graphs, and uploads.

## Next Sprint Suggestions

- Add controlled document ingestion after defining a safe parsing boundary.
- Add richer event timeline and trend visualization.
- Introduce authentication/roles only after demo workflow stabilizes.
- Replace the simulated device adapter with a USB serial adapter behind the same interface.
