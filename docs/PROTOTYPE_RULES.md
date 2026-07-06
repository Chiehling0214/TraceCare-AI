# Prototype Rules

All rules in this document are synthetic demonstration rules.
They are not validated clinical rules.

## RAPID_INCREASE

### Rule ID

RAPID_INCREASE

### Supported Test

creatinine

### Input

Two chronologically ordered laboratory results from the same patient.

### Prototype Trigger

Trigger when the dataset contains:

- Previous value: 0.8 mg/dL
- Current value: 1.3 mg/dL
- Time difference: 24 hours or less

### Output

- event_type: RAPID_LAB_CHANGE
- severity: REVIEW_REQUIRED
- status: OPEN

### Required Evidence Links

- Previous result: PREVIOUS_VALUE
- Current result: CURRENT_VALUE
- Both results: SUPPORTS

### Deduplication

The same pair of lab-result IDs must not create the same event twice.

### Safety

The output must use the wording:

"Prototype rule triggered. Human review is required."

It must not state that the patient has a diagnosis or requires treatment.

## ALLERGY_CONTRADICTION

### Rule ID

ALLERGY_CONTRADICTION

### Supported Facts

Fixed-format synthetic `ALLERGY_STATEMENT` facts only.

### Input

Two or more structured allergy facts from the same synthetic patient. Sprint 1 compares facts with the same `subject`.

### Prototype Trigger

Trigger when the same patient has both:

- a `PRESENT` allergy statement for a subject, and
- a `NEGATED` allergy statement for the same subject.

### Output

- event_type: CONTRADICTION
- severity: REVIEW_REQUIRED
- status: OPEN

### Required Evidence Links

Typed `EventEvidence` records must include:

- present fact: ASSERTED_FACT
- denied fact: DENIED_FACT
- both facts: SUPPORTS
- both source documents: SOURCE_DOCUMENT

### Deduplication

The same present-fact ID plus denied-fact ID must not create the same contradiction event twice.

### Safety

The output must use the wording:

"Prototype rule triggered. Human review is required."

It must not state that the patient has an allergy diagnosis, a confirmed chart error, or a treatment requirement.

## Sprint 2 Risk Fusion

Sprint 2 risk states are deterministic prototype review states. They are not diagnosis, prognosis, or treatment recommendations.

### Input

Unresolved clinical events for a synthetic patient.

Unresolved statuses:

- OPEN
- ACKNOWLEDGED
- DEFERRED

### Output

- risk_state: NORMAL, REVIEW_REQUIRED, or HIGH_RISK
- risk_reasons: rule reason codes plus related event IDs
- oldest_unresolved_event_at
- unresolved_event_count
- driver_event_ids

### Risk State Rules

- `NORMAL`: no unresolved events.
- `REVIEW_REQUIRED`: one or more unresolved events exist and no high-risk driver is present.
- `HIGH_RISK`: any unresolved event is `HIGH_RISK`, any `OPEN` event is at least 2 hours old, or multiple unresolved event types exist for the same patient.

### Timeout Rule

`POST /api/prototype/run-risk-evaluation` escalates an `OPEN` event to `HIGH_RISK` when its age is at least 2 hours at the supplied or current evaluation time.

Auto-escalation records exactly one `AUTO_ESCALATE` action per event.

### Safety

Risk messages must describe prototype workflow conditions only, such as unresolved events, multiple event types, or timeout. They must not say the patient has a disease, needs a treatment, or requires a real clinical escalation.

## Sprint 3 Evidence-first Summary Rules

Sprint 3 summaries are generated from an Evidence Package. They are not clinical recommendations and do not calculate risk.

### Evidence Package Inputs

- Synthetic patient identity
- Structured lab results
- Synthetic clinical documents
- Structured clinical facts
- Prototype clinical events
- Deterministic Sprint 2 risk output

### Summary Validation Rules

- Every returned sentence must include at least one evidence ID.
- Every evidence ID must exist in the Evidence Package.
- Numeric values in a sentence must also appear in the cited evidence text.
- Diagnosis and treatment language is rejected.
- If evidence is insufficient, the system abstains instead of summarizing.

### Abstention Rule

Sprint 3 requires at least two lab results and at least two synthetic documents for patient/handoff summaries. P003 intentionally fails this requirement and returns `INSUFFICIENT_LONGITUDINAL_SYNTHETIC_EVIDENCE`.

## Sprint 4 Device Alert Rules

Sprint 4 device output is a prototype alert display only. It must not control or be connected to any medical or treatment device.

### Adapter Rules

- `simulated` mode remains the default and must work without hardware.
- `usb_serial` mode may send commands only through the device adapter layer.
- API routes must not contain serial port logic.
- Missing serial dependency, missing port, timeout, or protocol error must return offline health with `fallback_active=true`.
- Frontend must display backend-returned device health and must not infer LED or buzzer state locally.

### Command Rules

- `PING` checks heartbeat.
- `SET` commands are idempotent and safe to repeat.
- Commands include `seq` and `protocol=tracecare-device-v1`.
- Frontend receives sanitized error codes only, such as `SERIAL_PORT_NOT_CONFIGURED`, `DEVICE_TIMEOUT`, or `DEVICE_PROTOCOL_ERROR`.

### State Mapping

| Backend state | LED | Buzzer |
| --- | --- | --- |
| `NORMAL` | `GREEN_SOLID` | `OFF` |
| `WARNING` | `YELLOW_BLINKING` | `SHORT_BEEP` |
| `ACKNOWLEDGED` | `YELLOW_SOLID` | `OFF` |
| `CRITICAL` | `RED_BLINKING` | `INTERMITTENT` |

## Sprint 5 Synthetic Import Rules

Sprint 5 imports are fixed-schema and synthetic-only.

### Lab CSV

- Only `.csv` files are accepted by filename.
- Required columns are defined by `tracecare-labs-csv-v1`.
- `patient_code` must begin with `P`.
- `test_name` must be `creatinine`.
- `unit` must be `mg/dL`.
- Numeric and datetime fields must parse before commit.
- Duplicate rows inside one file are invalid.
- Existing database duplicates are skipped with an explicit report.

### Document JSON

- Only `.json` files are accepted by filename.
- `schema_version` must be `tracecare-documents-json-v1`.
- Only fixed-format `documents[]` and structured `facts[]` are accepted.
- `fact_type` is limited to `ALLERGY_STATEMENT`.
- Source position fields are required and preserved.

### Transaction Rule

Import preview never writes patient, lab, document, fact, or event data. Import commit revalidates input and either commits all valid create/skip operations or records a failed import batch without partial imported records.

### Demo Management

Reset, seed, and run-demo endpoints are prototype/development-only. They must be repeatable and must not require manual database deletion.
