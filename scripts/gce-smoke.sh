#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8001}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:5176}"
API_URL="${BACKEND_URL}/api"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

echo "[1/7] Backend health"
curl --fail --silent --show-error "${BACKEND_URL}/health" > "${WORK_DIR}/health.json"

echo "[2/7] Frontend page"
curl --fail --silent --show-error "${FRONTEND_URL}" > "${WORK_DIR}/frontend.html"

echo "[3/7] Reset synthetic demo"
curl --fail --silent --show-error -X POST "${API_URL}/development/reset-demo" > "${WORK_DIR}/reset.json"

echo "[4/7] Seed synthetic demo"
curl --fail --silent --show-error -X POST "${API_URL}/development/seed-demo" > "${WORK_DIR}/seed.json"

echo "[5/7] Run deterministic demo analysis"
curl --fail --silent --show-error -X POST "${API_URL}/development/run-demo-analysis" > "${WORK_DIR}/analysis.json"

echo "[6/7] Verify patients and simulated device"
curl --fail --silent --show-error "${API_URL}/patients" > "${WORK_DIR}/patients.json"
curl --fail --silent --show-error "${API_URL}/device-state" > "${WORK_DIR}/device.json"

python3 - "${WORK_DIR}" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])

def read(name):
    return json.loads((root / name).read_text(encoding="utf-8"))

health = read("health.json")
patients_payload = read("patients.json")
device = read("device.json")

patients = patients_payload if isinstance(patients_payload, list) else patients_payload.get("items", [])
codes = {patient.get("patient_code") or patient.get("code") for patient in patients}

if health.get("status") not in {"ok", "healthy"}:
    raise SystemExit(f"Unexpected health payload: {health}")
if not {"P001", "P010"}.issubset(codes):
    raise SystemExit(f"Expected P001 and P010 after seed, got: {sorted(c for c in codes if c)}")
if device.get("adapter_mode") != "simulated":
    raise SystemExit(f"Expected simulated adapter, got: {device.get('adapter_mode')}")
if device.get("state") != "CRITICAL":
    raise SystemExit(f"Expected CRITICAL after demo analysis, got: {device.get('state')}")

print(f"Verified {len(patients)} synthetic patients; device={device.get('state')} ({device.get('adapter_mode')}).")
PY

echo "[7/7] PASS - GCE demo smoke completed"
