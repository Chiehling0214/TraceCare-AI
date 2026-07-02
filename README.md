# TraceCare AI

TraceCare AI is a local competition prototype for traceable clinical evidence and event lifecycle demonstration. Sprint 0 uses synthetic patients and deterministic creatinine trend rules to create review-required events. Sprint 1 adds fixed-format synthetic clinical documents, deterministic allergy contradiction detection, and an evidence graph. Sprint 2 adds deterministic risk fusion, event defer, timeout evaluation, and action history.

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
```

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
10. Confirm simulated device state follows unified risk priority.
11. Click `延後追蹤`; the event becomes `DEFERRED`, remains visible, and records a `DEFER` action.
12. Click `確認事件`; buzzer changes to off through `ACKNOWLEDGED` and records an `ACKNOWLEDGE` action.
13. Click `標示為已處理`; event becomes `RESOLVED`, records a `RESOLVE` action, and device state returns to `NORMAL` after all unresolved events are resolved.

## Notes

- Acknowledging an already acknowledged event returns the current state with `200 OK`.
- Resolving an `OPEN` event is allowed by the backend and sets `acknowledged_at` first, but the UI guides the preferred acknowledge-then-resolve demo flow.
- Deferring an event keeps it unresolved and visible. A missing `defer_until` defaults to four hours after the action time.
- Risk evaluation is deterministic. It never calls an LLM and does not produce diagnosis or treatment recommendations.
- No external AI, medical, or hardware APIs are called.
- Sprint 1 and Sprint 2 schema changes are additive. The prototype still uses SQLAlchemy `create_all`; Sprint 2 also includes a small additive SQLite migration helper for new nullable event lifecycle columns.
