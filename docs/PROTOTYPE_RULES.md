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
