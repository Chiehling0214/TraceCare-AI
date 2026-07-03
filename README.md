# TraceCare AI

TraceCare AI is a local competition prototype for traceable clinical evidence and event lifecycle demonstration. Sprint 0 uses synthetic patients and deterministic creatinine trend rules to create review-required events. Sprint 1 adds fixed-format synthetic clinical documents, deterministic allergy contradiction detection, and an evidence graph. Sprint 2 adds deterministic risk fusion, event defer, timeout evaluation, and action history. Sprint 3 adds evidence-first local summary APIs with deterministic fallback, citation validation, and numeric consistency checks. Sprint 4 adds optional ESP32 USB Serial alerting while preserving simulated device mode.

This project is a competition prototype and is not a medical device.
It must not be used for diagnosis or treatment decisions.
All included patient data is synthetic.

## Tech Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2, SQLite
- Frontend: React, TypeScript, Vite, Cytoscape.js, native CSS
- Tests: pytest and FastAPI TestClient

## Install

This repository includes working `.env` files for local Sprint 0 development:

- `.env` for Docker Compose
- `backend/.env` for the FastAPI backend
- `frontend/.env` for Vite

The default backend host port is `8001` because `8000` is commonly occupied on the local machine.

## Docker

```powershell
docker compose up --build
```

Open `http://localhost:5173`.

Docker Compose reads the root `.env` file. To change ports, edit:

```text
BACKEND_HOST_PORT=8001
FRONTEND_HOST_PORT=5173
VITE_API_BASE_URL=http://localhost:8001/api
LLM_MODE=disabled
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=
LOCAL_LLM_TIMEOUT_SECONDS=120
DEVICE_ADAPTER_MODE=simulated
DEVICE_SERIAL_PORT=
DEVICE_SERIAL_BAUD_RATE=115200
DEVICE_SERIAL_TIMEOUT_SECONDS=1.0
DEVICE_HEARTBEAT_TIMEOUT_SECONDS=3.0
```

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Frontend:

```powershell
cd frontend
npm install
```

## Backend

Start the API:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Seed synthetic data:

```powershell
cd backend
python -m app.seed_cli
```

Run analysis:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8001/api/prototype/run-analysis
Invoke-RestMethod -Method Post http://127.0.0.1:8001/api/prototype/run-contradiction-analysis
Invoke-RestMethod -Method Post http://127.0.0.1:8001/api/prototype/run-risk-evaluation
Invoke-RestMethod -Method Post http://127.0.0.1:8001/api/patients/1/summaries/patient
```

## Local Summary Mode

Sprint 3 defaults to deterministic fallback mode:

```text
LLM_MODE=disabled
```

Optional local-only Ollama mode can be configured with:

```text
LLM_MODE=ollama
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=<local-model-name>
LOCAL_LLM_TIMEOUT_SECONDS=120
```

External generative AI APIs are not used. If no local runtime is available, the app still returns validated deterministic fallback summaries or abstains when evidence is insufficient.

## Device Adapter Mode

Sprint 4 defaults to simulated device mode:

```text
DEVICE_ADAPTER_MODE=simulated
```

Optional ESP32 USB Serial mode:

```text
DEVICE_ADAPTER_MODE=usb_serial
DEVICE_SERIAL_PORT=COM3
DEVICE_SERIAL_BAUD_RATE=115200
DEVICE_SERIAL_TIMEOUT_SECONDS=1.0
DEVICE_HEARTBEAT_TIMEOUT_SECONDS=3.0
```

Do not hard-code a COM port in source code. Hardware failure or missing serial configuration does not block the dashboard; the backend returns `fallback_active=true` and the UI shows laptop fallback status. The command protocol is documented in `docs/DEVICE_PROTOCOL.md`, and the ESP32 sketch is tracked at `firmware/esp32_tracecare_alert/esp32_tracecare_alert.ino`.

## Frontend

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`.

## Tests

```powershell
cd backend
pytest
```

## Demo Flow

1. Start the backend.
2. Run `python -m app.seed_cli`.
3. Start the frontend.
4. Click `執行原型分析`; the UI runs lab trend analysis, contradiction analysis, and deterministic risk evaluation.
5. Confirm P001 appears before normal patients and shows prototype risk reasons.
6. Open P001 detail.
7. Review `0.8 -> 1.3 mg/dL`, `RAPID_INCREASE`, and lab source documents.
8. Review synthetic clinical documents, structured allergy facts, `ALLERGY_CONTRADICTION`, and source positions.
9. Inspect the Evidence Graph section for patient, document, fact, lab, and event relationships.
10. In the Evidence-first Summary panel, click `病人摘要` or `交班摘要`.
11. Confirm each returned sentence shows citation chips such as `lab:1`, `fact:1`, `event:1`, or `risk:1`.
12. Confirm device state follows unified risk priority in simulated mode, or shows USB Serial health and laptop fallback when hardware is offline.
13. Click `延後追蹤`; the event becomes `DEFERRED`, remains visible, and records a `DEFER` action.
14. Click `確認事件`; buzzer changes to off through `ACKNOWLEDGED` and records an `ACKNOWLEDGE` action.
15. Click `標示為已處理`; event becomes `RESOLVED`, records a `RESOLVE` action, and device state returns to `NORMAL` after all unresolved events are resolved.

## Notes

- Acknowledging an already acknowledged event returns the current state with `200 OK`.
- Resolving an `OPEN` event is allowed by the backend and sets `acknowledged_at` first, but the UI guides the preferred acknowledge-then-resolve demo flow.
- Deferring an event keeps it unresolved and visible. A missing `defer_until` defaults to four hours after the action time.
- Risk evaluation is deterministic. It never calls an LLM and does not produce diagnosis or treatment recommendations.
- Sprint 3 summaries do not calculate risk or update events. Risk context comes from Sprint 2 deterministic services.
- Every returned summary sentence must cite evidence IDs. Validation rejects missing citations and numeric mismatches.
- Sprint 4 physical alerting is optional and local-only. It is a non-medical demo alert device and must not control any medical or treatment equipment.
- No external AI, medical, or hospital APIs are called.
- Sprint 1 and Sprint 2 schema changes are additive. The prototype still uses SQLAlchemy `create_all`; Sprint 2 also includes a small additive SQLite migration helper for new nullable event lifecycle columns.
