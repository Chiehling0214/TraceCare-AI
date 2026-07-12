# Sprint 6 Validation Results

Generated from `python -m app.sprint6_validation` on 2026-07-07 using fixed synthetic data.

## Environment

- Database: in-memory SQLite
- Dataset: `tracecare-sprint6-validation-v1`
- Patients: `P001`, `P002`, `P003`, `P010`, `P011`
- LLM: deterministic fallback
- Device: simulated adapter
- Synthetic data only: yes

## Metrics

| Metric | Cases | Result |
|---|---:|---|
| RAPID_INCREASE rule accuracy | 5 | 1.0 |
| RAPID_INCREASE precision / recall / F1 | 5 | 1.0 / 1.0 / 1.0 |
| ALLERGY_CONTRADICTION accuracy | 5 | 1.0 |
| ALLERGY_CONTRADICTION precision / recall / F1 | 5 | 1.0 / 1.0 / 1.0 |
| Event acknowledge/resolve synchronization | 6 actions | 1.0 success rate |
| Summary validation failure rate | 2 cases | 0.0 |
| Summary abstention rate | 2 cases | 0.5 |
| Summary evidence coverage | 2 cases | 0.421053 |
| Simulated device state checks | 2 | 1.0 success rate |
| Run-demo analysis latency | 5 patients | 24.842 ms |

## NOT VERIFIED

- Real ESP32 LED/buzzer/heartbeat latency was not verified.
- Real local LLM inference was not verified in this Sprint 6 validation run.
- Browser-driven E2E was not configured; Sprint 6 adds API-level demo workflow coverage instead.

## Docker Smoke

- `docker compose up --build -d`: PASS after Docker Desktop became available.
- Backend health `http://localhost:8001/health`: 200.
- Frontend `http://localhost:5176`: 200.
- Docker demo reset/seed/run-analysis: PASS.
- Post-analysis state: `P001` is `HIGH_RISK`, `P010` is `REVIEW_REQUIRED`, simulated device state is `CRITICAL`.

## Limitations

- Metrics are prototype metrics from a small fixed synthetic dataset.
- Deterministic rules are expected to score perfectly on these exact fixtures.
- Summary quality is measured by validation/fallback behavior, citation presence, and coverage, not clinical usefulness.
- Device validation covers backend-derived simulated adapter state only.
