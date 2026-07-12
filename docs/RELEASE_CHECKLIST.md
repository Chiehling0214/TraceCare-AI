# TraceCare AI Competition Release Checklist

Run this checklist on the presentation machine and network before every judged demo. Use synthetic data only.

## 1. Configuration Preflight

- [ ] Docker Desktop is running.
- [ ] Root `.env` has the intended `BACKEND_HOST_PORT` and `FRONTEND_HOST_PORT`.
- [ ] `VITE_API_BASE_URL` points to the backend host port.
- [ ] `DEMO_MANAGEMENT_ENABLED=true`.
- [ ] `DEVICE_ADAPTER_MODE=simulated` unless real ESP32 has already passed hardware preflight.
- [ ] For Ollama: `LLM_MODE=ollama`, base URL is reachable from the backend container, and the configured model is installed.
- [ ] For guaranteed no-model fallback: `LLM_MODE=disabled`.
- [ ] No real patient files, records, names, identifiers, screenshots, or browser history are visible.

Current repository defaults in the root `.env` use frontend `5176` and backend `8001`.

## 2. Service Preflight

Run:

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://localhost:8001/health
(Invoke-WebRequest http://localhost:5176 -UseBasicParsing).StatusCode
```

- [ ] Backend container is running and `/health` returns success.
- [ ] Frontend container is running and returns HTTP 200.
- [ ] Patient overview loads without the offline banner.
- [ ] Browser console is not needed during the presentation.

## 3. Demo Data Preflight

On `http://localhost:5176/demo-data`, run in this order:

- [ ] `Reset Demo` succeeds.
- [ ] `Seed Demo` succeeds and reports five synthetic patients.
- [ ] `Run Demo Analysis` succeeds and reports three created events on a fresh fixture.
- [ ] Refreshing the overview shows P001 and P010.

Do not run analysis repeatedly between preflight and presentation unless the demo is reset and seeded again.

## 4. Expected UI States

- [ ] Global prototype notice says the app is not a medical device and data is synthetic.
- [ ] P001 is `HIGH_RISK` after the standard demo analysis.
- [ ] P010 is `REVIEW_REQUIRED` after the standard demo analysis.
- [ ] P001 detail shows the 0.8 -> 1.3 mg/dL synthetic creatinine evidence.
- [ ] Event detail exposes evidence and lifecycle controls.
- [ ] Evidence Graph renders patient/evidence/event relationships.
- [ ] Summary panel displays evidence IDs for every returned sentence.
- [ ] Summary status clearly identifies Ollama, deterministic fallback, or rejection.
- [ ] Device state is backend-derived and shows the active adapter mode.
- [ ] Acknowledge and resolve actions update state and audit history.

## 5. Ollama Preflight (Optional)

From the host:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags', timeout=5).status)"
```

- [ ] Host Ollama responds.
- [ ] Backend container can reach host Ollama.
- [ ] Configured model name exactly matches an installed model.
- [ ] At least one patient and one handoff summary have been tried before presenting.
- [ ] Presenter is prepared to explain fallback or rejection honestly.

## 6. ESP32 Preflight (Optional)

- [ ] Firmware from `firmware/esp32_tracecare_alert/esp32_tracecare_alert.ino` is flashed.
- [ ] Correct COM port is configured; it is not hard-coded in source.
- [ ] No Arduino Serial Monitor or other process is holding the COM port.
- [ ] `PING` returns the expected `PONG` protocol response.
- [ ] NORMAL, WARNING, CRITICAL, and ACKNOWLEDGED states produce the expected LED/buzzer behavior.
- [ ] Disconnect is shown as hardware unavailable and laptop fallback remains usable.
- [ ] Reconnect succeeds before choosing `DEVICE_ADAPTER_MODE=usb_serial` for the presentation.

On Windows Docker Desktop, direct COM access from a Linux container is not the default path. Run the backend locally on Windows for real USB Serial validation, or use simulated mode for the Docker competition demo.

## 7. Failure Recovery

### Docker Is Not Running

1. Start Docker Desktop.
2. Run `docker compose up --build -d`.
3. Repeat service and data preflight.

If Docker cannot recover in the presentation window, use screenshots only and state that the live environment is unavailable. Do not invent live results.

### Backend Is Unavailable

1. Confirm `docker compose ps`.
2. Run `docker compose logs --tail 100 backend` off-screen.
3. Run `docker compose restart backend`.
4. Recheck `/health`, then use the UI retry action.

### Frontend Is Unavailable

1. Confirm backend `/health` first.
2. Run `docker compose logs --tail 100 frontend` off-screen.
3. Run `docker compose restart frontend`.
4. Reload the page without clearing demo data.

### Ollama Is Unavailable or Output Is Rejected

1. Continue the deterministic event/evidence demo.
2. Explain that the summary dependency is optional and validated.
3. Use deterministic fallback; if necessary set `LLM_MODE=disabled` and restart backend.
4. Never bypass summary validation to force generated text on screen.

### ESP32 Is Offline

1. Keep the dashboard and lifecycle demo running.
2. State that laptop fallback is active.
3. Switch to `DEVICE_ADAPTER_MODE=simulated` and restart backend if reconnection is unreliable.
4. Do not claim simulated state as physical hardware verification.

### Demo Data Is Unexpected

1. Open `/demo-data`.
2. Run Reset -> Seed -> Run Demo Analysis.
3. Return to overview and refresh.

## 8. Presentation Safety Review

- [ ] Say “prototype rule” rather than “clinical diagnosis.”
- [ ] Say “review-required event” rather than “confirmed medical alert.”
- [ ] Say “synthetic fixture result” rather than “clinical accuracy.”
- [ ] Say “local-only assisted summary” rather than “AI medical decision.”
- [ ] Identify simulated hardware whenever simulated mode is active.
- [ ] Do not make claims about real hospital integration, FHIR, arbitrary document parsing, or production readiness.
- [ ] Do not show or request diagnosis or treatment recommendations.

## 9. Final Release Gate

- [ ] Backend regression tests pass or any environment-only runner limitation is documented.
- [ ] Frontend type check passes.
- [ ] Frontend production build passes.
- [ ] Docker Compose smoke passes after the final documentation change.
- [ ] `docs/DEMO_SCRIPT.md` matches observed UI behavior.
- [ ] `docs/JUDGE_QA.md` contains no unverified product claims.
- [ ] Presenter has rehearsed the selected duration once with a timer.
- [ ] Git working tree and intended competition checkpoint are recorded.

