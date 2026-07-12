# TraceCare AI Competition Demo Script

All demonstrations use synthetic data. TraceCare AI is a competition prototype, not a medical device, and must not be used for diagnosis or treatment decisions.

## Before Going On Stage

Complete `docs/RELEASE_CHECKLIST.md`. Keep these tabs open:

1. Patient overview: `http://localhost:5176/`
2. Demo Data: `http://localhost:5176/demo-data`
3. Patient P001 detail, opened after seeding

Use browser zoom at 90% or 100%. Keep Docker logs and terminals off the projected screen. Unless real ESP32 validation is part of the presentation, use `DEVICE_ADAPTER_MODE=simulated`.

## Core Story

TraceCare AI does three separate jobs:

1. Deterministic rules detect prototype evidence patterns and calculate workflow risk.
2. An evidence graph and audit trail show why an event exists and what reviewers did.
3. A local-only LLM may phrase an evidence-cited summary, but it never calculates risk or changes an event. A deterministic fallback keeps the demo available without the model.

## 3-Minute Script

### 0:00-0:30 - Problem and Safety Boundary

**Show:** Patient overview and the prototype safety notice.

**Say:**

> TraceCare AI is an evidence-traceability prototype using synthetic data only. It does not diagnose or recommend treatment. Its purpose is to detect predefined evidence patterns, make the reason reviewable, and keep every workflow action traceable.

### 0:30-1:15 - Deterministic Detection

**Do:** Open `Demo Data`, then run `Reset Demo`, `Seed Demo`, and `Run Demo Analysis`. Return to the overview.

**Expect:** P001 is `HIGH_RISK`; P010 is `REVIEW_REQUIRED`; the device state is derived from backend risk.

**Say:**

> The demo is reproducible. Reset removes the synthetic demo set, seed recreates it idempotently, and analysis runs deterministic prototype rules. P001 is prioritized because its synthetic creatinine changes from 0.8 to 1.3 mg/dL within 24 hours. P010 demonstrates a structured allergy contradiction. These decisions do not come from an LLM.

### 1:15-2:10 - Evidence and Lifecycle

**Do:** Open P001. Point to labs, event evidence, Evidence Graph, and action controls. Acknowledge one open event.

**Expect:** The event becomes `ACKNOWLEDGED`, an audit action appears, and the buzzer state becomes off through backend-provided device state.

**Say:**

> Every event links back to source evidence. The graph connects patient, lab, document, fact, and event nodes. Acknowledging the event records an action instead of deleting history. The frontend does not invent the LED or buzzer state; it displays the state returned by the backend.

### 2:10-2:45 - Evidence-First Summary

**Do:** Generate `病人摘要`.

**Expect:** Each returned sentence has evidence ID chips. The status is either validated Ollama output or deterministic fallback.

**Say:**

> The local-only model is limited to wording evidence already selected by the backend. Every sentence must cite evidence IDs and pass citation and numeric validation. If Ollama is unavailable or validation fails, the system rejects that output and uses a clearly labelled deterministic fallback where possible.

### 2:45-3:00 - Close

**Say:**

> The key result is not autonomous clinical decision-making. It is a reproducible, inspectable workflow: deterministic detection, source-linked evidence, auditable actions, and local-only assisted summarization with a safe fallback.

## 5-Minute Script

Use the 3-minute script and add these segments.

### Add After Deterministic Detection - Compare Two Event Types

**Do:** Briefly open P010 after P001.

**Expect:** P010 shows an `ALLERGY_CONTRADICTION` linked to fixed-format synthetic document facts.

**Say:**

> The rule layer supports different evidence types through the same event workflow. Lab trend detection compares structured measurements; contradiction detection compares normalized facts extracted from fixed-format synthetic documents. Arbitrary medical document parsing is outside this prototype.

### Add After Lifecycle - Resolve and Confirm Device State

**Do:** Resolve acknowledged events and return to the overview.

**Expect:** Resolved events remain auditable. Device priority decreases only when no higher-priority unresolved event remains.

**Say:**

> Resolve is a workflow action, not deletion. Device state follows unresolved deterministic risk. The simulated adapter is always available; the optional ESP32 adapter uses the same backend state and can fall back without blocking the dashboard.

### Add Before Close - Validation Evidence

**Show:** `docs/SPRINT_06_VALIDATION_RESULTS.md`, only if a judge asks for measurements.

**Say:**

> The fixed synthetic validation fixture produced F1 1.0 for both included prototype rules and 100% synchronization for the tested lifecycle and simulated-device cases. These are fixture-level prototype results, not clinical performance claims. Real-world clinical validation is not complete.

## 10-Minute Script

Use the 5-minute script, then add the following details and allow questions during transitions.

### Architecture Separation - 90 Seconds

**Show:** Patient detail, not source code.

**Say:**

> The backend separates deterministic rules, risk fusion, lifecycle, evidence package construction, LLM adaptation, output validation, and device adaptation. The API coordinates these services. The LLM cannot update risk or event state, and the serial driver is isolated behind the device adapter.

Explain the flow:

`synthetic source -> deterministic rule -> event/evidence -> deterministic risk -> UI/device state`

The summary branch starts only after evidence exists:

`evidence package -> local model or fallback -> validator -> cited sentences or rejection`

### Import Safety and Repeatability - 60 Seconds

**Do:** On Demo Data, show a CSV or JSON preview without committing a new import.

**Expect:** The page says synthetic-only; validation results appear before commit.

**Say:**

> Import accepts only fixed-schema synthetic CSV and JSON. Preview validates required fields, types, timestamps, and units before a transaction. Duplicate source records are not recreated, and failed imports roll back instead of leaving partial data.

### Failure Demonstration - 60 Seconds

Do not intentionally stop Docker during the judged demo. Explain the tested degradation path:

> Backend loss produces a visible offline state with retry. Ollama loss uses deterministic fallback or explicit abstention. ESP32 loss activates laptop fallback while the dashboard and event lifecycle continue. The simulated device mode is the competition fallback.

### Limitations - 45 Seconds

**Say:**

> This prototype uses SQLite, fixed synthetic documents, predefined rules, and optional local Ollama and ESP32 integrations. It has no production authentication, no live HIS, LIS, EMR, or FHIR integration, no arbitrary PDF or Word parsing, and no clinical validation. It must not receive real patient data.

### Close and Q&A

Use `docs/JUDGE_QA.md` for detailed questions. Keep answers scoped to what has actually been implemented and verified.

## Expected Main Demo States

| Point in flow | Expected UI state |
|---|---|
| After reset | Demo operation succeeds; demo patients are removed |
| After seed | Five synthetic patients are available |
| After run analysis | Three prototype events are created on a fresh seeded dataset |
| Overview | P001 `HIGH_RISK`; P010 `REVIEW_REQUIRED` |
| P001 detail | Synthetic labs, events, evidence graph, lifecycle controls |
| Summary | Evidence IDs on every sentence; generated or fallback status clearly labelled |
| Device | Backend-derived `CRITICAL` while high-risk event is unresolved |
| After acknowledge | Event audit contains `ACKNOWLEDGE`; buzzer is off for acknowledged state |
| After all relevant resolves | No unresolved high-priority event; device returns toward `NORMAL` |

Exact counts assume a successful Reset -> Seed -> Run Demo Analysis sequence with the repository fixture.

