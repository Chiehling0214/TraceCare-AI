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
