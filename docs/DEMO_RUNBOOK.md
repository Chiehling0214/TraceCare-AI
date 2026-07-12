# TraceCare AI Demo Runbook

This runbook uses only synthetic data. TraceCare AI is a prototype and is not a medical device.

## Local Docker Demo

1. Configure root `.env`.
2. Start services:

```powershell
docker compose up --build
```

3. Open `http://localhost:5176` or the `FRONTEND_HOST_PORT` configured in `.env`.
4. Open `/demo-data`.
5. Click `Reset Demo`.
6. Click `Seed Demo`.
7. Click `Run Demo Analysis`.
8. Open the patient overview.
9. Confirm `P001` is high risk and `P010` has a review-required contradiction event.
10. Open `P001`.
11. Review labs, documents, facts, events, Evidence Graph, and Evidence-first Summary.
12. Click acknowledge and resolve actions.
13. Confirm device state changes through backend-derived state.

## Validation Command

Run fixed synthetic validation metrics:

```powershell
cd backend
set PYTHONPATH=D:\coding\TraceCare-AI\backend\.deps;D:\coding\TraceCare-AI\backend
C:\Users\beard\anaconda3\python.exe -m app.sprint6_validation
```

The runner uses in-memory SQLite, deterministic fallback summaries, and simulated device mode.

## Failure Fallbacks

- Backend unavailable: frontend shows retry/offline messaging. Restart FastAPI or Docker Compose.
- Frontend unavailable: restart frontend container or Vite dev server.
- Local LLM unavailable: summary API uses deterministic fallback or abstains.
- ESP32 unavailable: keep `DEVICE_ADAPTER_MODE=simulated` or allow USB Serial fallback; dashboard remains usable.
- Demo data inconsistent: use `/demo-data` Reset Demo, Seed Demo, then Run Demo Analysis.

## Safety

- Do not use real patient data.
- Do not paste real medical records into import fields.
- Do not use outputs for diagnosis or treatment decisions.
- Do not connect ESP32 output to medical or treatment devices.

## Competition Package

- Follow `docs/DEMO_SCRIPT.md` for timed 3-, 5-, or 10-minute presentations.
- Use `docs/JUDGE_QA.md` for implementation, validation, and limitation questions.
- Complete `docs/RELEASE_CHECKLIST.md` on the presentation machine before the judged demo.
