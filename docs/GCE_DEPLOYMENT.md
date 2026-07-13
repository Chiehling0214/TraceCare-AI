# TraceCare AI GCE Demo Deployment

This runbook deploys the competition prototype to one Google Compute Engine VM. It uses synthetic data only, is not a medical device, and is not a production hospital deployment.

## Deployment Status

The repository contains a reproducible GCE configuration, but no real GCE VM was available during Sprint 8 implementation. Commands under **Observed Verification** distinguish local checks from cloud checks that remain `NOT VERIFIED`.

## Architecture and Security Boundary

The demo exposes two ports directly from one VM:

- `5176`: Vite frontend
- `8001`: FastAPI backend, required by the browser

The backend includes unauthenticated development reset/seed/run endpoints. Restrict both ports to the presenter or judging network CIDR. Do not use `0.0.0.0/0` for a persistent demo VM. HTTPS, authentication, managed databases, and production hardening are outside Sprint 8.

The SQLite database is stored in the Docker named volume `tracecare-ai_backend_data`. The cloud path always uses `DEVICE_ADAPTER_MODE=simulated`; a GCE VM cannot use an ESP32 connected to the presenter's laptop.

## VM Decision Matrix

Confirm current availability and pricing in the selected region before creation.

| Mode | Starting recommendation | Purpose | Notes |
|---|---|---|---|
| App-only | `e2-standard-2`, 2 vCPU, 8 GB RAM, 30 GB balanced disk | Recommended backup demo | Runs app with deterministic summary fallback |
| App + CPU Ollama | `e2-standard-4`, 4 vCPU, 16 GB RAM, 50 GB disk | Optional small local model | Slower generation; benchmark before judging |
| App + GPU Ollama | `g2-standard-4` with one L4 where available, 100 GB disk | Optional faster local inference | Requires GPU quota, driver setup, higher cost |

E2 does not support attached GPUs. GPU machine type availability, quota, and price vary by zone. Do not reserve GPU capacity unless Sprint 9 model verification justifies it.

Official references:

- Google Compute Engine machine families: <https://cloud.google.com/compute/docs/general-purpose-machines>
- Google GPU VM overview: <https://cloud.google.com/compute/docs/gpus/create-vm-with-gpus>
- Google VPC firewall rules: <https://cloud.google.com/firewall/docs/using-firewalls>
- Google Cloud pricing calculator: <https://cloud.google.com/products/calculator>
- Docker Engine on Ubuntu: <https://docs.docker.com/engine/install/ubuntu/>

## 1. Create an App-Only VM from Cloud Shell

Set project-specific values. `PRESENTER_IP` must be a CIDR such as `203.0.113.10/32`.

```bash
export PROJECT_ID="your-project-id"
export ZONE="asia-east1-b"
export VM_NAME="tracecare-demo"
export PRESENTER_IP="YOUR_PUBLIC_IP/32"

gcloud config set project "${PROJECT_ID}"
gcloud compute instances create "${VM_NAME}" \
  --zone="${ZONE}" \
  --machine-type=e2-standard-2 \
  --image-family=ubuntu-2404-lts-amd64 \
  --image-project=ubuntu-os-cloud \
  --boot-disk-type=pd-balanced \
  --boot-disk-size=30GB \
  --tags=tracecare-demo
```

Reserve a static external IP for a stable demo URL, or read the ephemeral IP after creation. An ephemeral IP can change after stop/start.

```bash
export GCE_PUBLIC_IP="$(gcloud compute instances describe "${VM_NAME}" --zone="${ZONE}" --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"
echo "${GCE_PUBLIC_IP}"
```

## 2. Restrict Firewall Access

```bash
gcloud compute firewall-rules create tracecare-demo-ui \
  --network=default \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:5176,tcp:8001 \
  --source-ranges="${PRESENTER_IP}" \
  --target-tags=tracecare-demo
```

Add each required judging CIDR deliberately. Delete or narrow the rule immediately after the demo. If the presenter network changes, update `--source-ranges` before opening ports globally.

## 3. Install Docker on Ubuntu

SSH to the VM:

```bash
gcloud compute ssh "${VM_NAME}" --zone="${ZONE}"
```

Follow Docker's current official Ubuntu repository instructions. The following is the supported apt-repository flow at the time this runbook was written:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker run --rm hello-world
```

The remaining commands use `sudo docker` so logging out is not required to refresh group membership.

## 4. Clone and Configure

```bash
git clone https://github.com/Chiehling0214/TraceCare-AI.git
cd TraceCare-AI
cp .env.gce.example .env
```

Edit `.env` and replace both `GCE_PUBLIC_IP` placeholders with the VM external IP:

```text
FRONTEND_ORIGIN=http://YOUR_VM_IP:5176
VITE_API_BASE_URL=http://YOUR_VM_IP:8001/api
```

Keep these defaults for the app-only deployment:

```text
SEED_ON_STARTUP=false
LLM_MODE=disabled
DEVICE_ADAPTER_MODE=simulated
DEMO_MANAGEMENT_ENABLED=true
```

Do not commit `.env`. Do not upload real patient data or private model credentials.

## 5. Validate and Start

Always include both Compose files on GCE:

```bash
sudo docker compose -f docker-compose.yml -f docker-compose.gce.yml config
sudo docker compose -f docker-compose.yml -f docker-compose.gce.yml up --build -d
sudo docker compose -f docker-compose.yml -f docker-compose.gce.yml ps
```

Wait until both services report healthy. Inspect failures without exposing logs on the projected screen:

```bash
sudo docker compose -f docker-compose.yml -f docker-compose.gce.yml logs --tail=100 backend
sudo docker compose -f docker-compose.yml -f docker-compose.gce.yml logs --tail=100 frontend
```

## 6. Run the GCE Smoke Test

On the VM:

```bash
chmod +x scripts/gce-smoke.sh
./scripts/gce-smoke.sh
```

The script verifies backend health, frontend response, reset, seed, deterministic analysis, P001/P010 presence, and simulated `CRITICAL` device state. It mutates only the synthetic demo database.

From the intended presentation machine, separately verify:

```powershell
Invoke-RestMethod http://YOUR_VM_IP:8001/health
(Invoke-WebRequest http://YOUR_VM_IP:5176 -UseBasicParsing).StatusCode
```

Then follow `docs/RELEASE_CHECKLIST.md` and the patient-detail walkthrough in `docs/DEMO_SCRIPT.md`.

## 7. Optional Ollama Decision

The recommended GCE backup demo keeps `LLM_MODE=disabled`. This verifies deterministic fallback and avoids model startup latency and GPU cost.

For CPU Ollama:

1. Resize to at least the selected model's measured CPU/RAM requirement.
2. Install Ollama on the VM host from its official distribution.
3. Bind Ollama to an interface reachable from Docker without opening port `11434` in the GCE firewall.
4. Keep `LOCAL_LLM_BASE_URL=http://host.docker.internal:11434`; the GCE Compose override maps the Linux host gateway.
5. Set the exact installed model name and run Sprint 9 validation before using it live.

For GPU Ollama, also install a supported NVIDIA driver/container path and verify quota, model memory, cold-start time, and cost. Sprint 8 does not claim either model path as verified.

## 8. Update and Restart

```bash
cd ~/TraceCare-AI
git pull --ff-only
sudo docker compose -f docker-compose.yml -f docker-compose.gce.yml up --build -d
./scripts/gce-smoke.sh
```

Never pull over uncommitted VM edits. Keep environment changes only in ignored `.env`.

## 9. Backup and Restore the Demo Volume

This is optional because Reset -> Seed -> Run Demo Analysis recreates the synthetic fixture.

Backup while services are stopped for a consistent SQLite copy:

```bash
mkdir -p ~/tracecare-backups
sudo docker compose -f docker-compose.yml -f docker-compose.gce.yml stop backend
sudo docker run --rm \
  -v tracecare-ai_backend_data:/data:ro \
  -v "${HOME}/tracecare-backups:/backup" \
  alpine:3.20 tar czf /backup/tracecare-demo-volume.tgz -C /data .
sudo docker compose -f docker-compose.yml -f docker-compose.gce.yml start backend
```

Restore only synthetic prototype data into an empty/recreated demo volume. Do not use backup archives as a substitute for versioned fixtures.

## 10. Failure Recovery

- Backend unhealthy: inspect backend logs, confirm `.env`, then restart backend.
- Frontend unreachable: confirm firewall source CIDR and frontend health before changing application code.
- Browser CORS error: ensure `FRONTEND_ORIGIN` exactly matches `http://PUBLIC_IP:5176`, with no trailing slash.
- Frontend calls localhost: rebuild frontend after correcting `VITE_API_BASE_URL`; Vite reads it when the container starts/builds.
- Ollama unavailable: set `LLM_MODE=disabled`, recreate backend, and use deterministic fallback.
- Unexpected data: run `./scripts/gce-smoke.sh` or UI Reset -> Seed -> Run Demo Analysis.
- VM reboot: Compose services use `restart: unless-stopped`; verify health after boot.

## 11. Cost Control and Teardown

Stopping a VM stops vCPU/RAM charges but attached disk and reserved external IP charges can continue. Deletion is the clean end of a temporary demo. Confirm current prices in the Google Cloud pricing calculator rather than relying on static estimates.

Stop when retaining the disk intentionally:

```bash
gcloud compute instances stop "${VM_NAME}" --zone="${ZONE}"
```

Delete the firewall and VM after exporting anything intentionally retained:

```bash
gcloud compute firewall-rules delete tracecare-demo-ui --quiet
gcloud compute instances delete "${VM_NAME}" --zone="${ZONE}" --quiet
```

Also release any separately reserved static IP and delete snapshots/backups no longer required. Check Billing reports after teardown.

## Observed Verification

| Check | Result |
|---|---|
| Base `docker compose config` on Windows | PASS |
| GCE override config merge | PASS with `.env.gce.example`; health checks, restart policies, host gateway, ports, and environment resolved correctly |
| Backend regression tests | PASS, 55 tests; 2 existing FastAPI startup deprecation warnings |
| Frontend TypeScript check and production build | PASS; 58 modules transformed |
| Smoke script API contract review | PASS against current health, patient-list, and device-state schemas |
| Local Docker build/start with GCE override | PASS; backend and frontend reported healthy |
| Local backend/frontend access | PASS; backend `/health` returned `ok`, frontend returned HTTP 200 |
| Local reset/seed/run-demo smoke | PASS; 5 synthetic patients, P001 `HIGH_RISK`, P010 `REVIEW_REQUIRED` |
| Local simulated device verification | PASS; backend returned `CRITICAL` with adapter `simulated` |
| Real GCE VM creation | NOT VERIFIED; `gcloud` and GCE credentials unavailable |
| Remote frontend/backend access | NOT VERIFIED |
| GCE reset/seed/run-demo | NOT VERIFIED |
| GCE deterministic fallback | NOT VERIFIED |
