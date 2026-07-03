# TraceCare AI — Sprint 0 API Specification

## 1. Purpose

This document defines the backend API contract for **Sprint 0** of TraceCare AI.

Sprint 0 supports only:

- Synthetic patients
- Structured creatinine laboratory results
- Deterministic prototype analysis
- Clinical event creation
- Evidence tracing
- Event acknowledgement and resolution
- Simulated device state

The API must not provide:

- Medical diagnosis
- Treatment recommendations
- Real patient data integration
- LLM or RAG functionality
- FHIR integration
- Real ESP32 communication

---

## 2. Base URL

Local development:

```text
http://localhost:8000
```

All application endpoints except `/health` use the `/api` prefix.

---

## 3. Content Type

Requests and responses use JSON unless otherwise specified.

```http
Content-Type: application/json
```

---

## 4. General Conventions

### 4.1 Date and Time

All timestamps must use ISO 8601 format.

Example:

```text
2026-06-21T08:00:00Z
```

The backend should store timestamps in UTC.

### 4.2 Identifiers

- Internal resource IDs are integers.
- `patient_code` is a stable synthetic identifier such as `P001`.
- Database IDs must not be reused.

### 4.3 Synthetic Data Notice

All patient responses should make it possible for the frontend to identify the data as synthetic.

Recommended field:

```json
{
  "is_synthetic": true
}
```

---

## 5. Enumerations

### 5.1 Event Type

```text
RAPID_LAB_CHANGE
```

### 5.2 Event Severity

```text
NORMAL
REVIEW_REQUIRED
HIGH_RISK
```

Sprint 0 analysis creates `REVIEW_REQUIRED` events only.

### 5.3 Event Status

```text
OPEN
ACKNOWLEDGED
DEFERRED
RESOLVED
```

### 5.4 Evidence Relation Type

```text
SUPPORTS
PREVIOUS_VALUE
CURRENT_VALUE
```

### 5.5 Device State

```text
NORMAL
WARNING
CRITICAL
ACKNOWLEDGED
```

### 5.6 LED State

```text
GREEN_SOLID
YELLOW_BLINKING
YELLOW_SOLID
RED_BLINKING
```

### 5.7 Buzzer State

```text
OFF
SHORT_BEEP
INTERMITTENT
```

---

## 6. Standard Error Response

All API errors should use the following structure:

```json
{
  "error": {
    "code": "PATIENT_NOT_FOUND",
    "message": "Patient 999 was not found."
  }
}
```

Recommended error codes:

```text
PATIENT_NOT_FOUND
EVENT_NOT_FOUND
INVALID_EVENT_TRANSITION
VALIDATION_ERROR
ANALYSIS_FAILED
INTERNAL_SERVER_ERROR
```

---

# 7. Health API

## 7.1 Health Check

### Request

```http
GET /health
```

### Success Response

Status: `200 OK`

```json
{
  "status": "ok",
  "service": "tracecare-ai-backend",
  "version": "0.1.0"
}
```

---

# 8. Patient APIs

## 8.1 List Patients

### Request

```http
GET /api/patients
```

### Query Parameters

None required.

Optional future-compatible parameters may include:

```text
severity
status
limit
offset
```

Do not implement advanced filtering unless it is simple and does not expand Sprint 0 scope.

### Success Response

Status: `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "patient_code": "P001",
      "display_name": "Synthetic Patient A",
      "is_synthetic": true,
      "current_severity": "REVIEW_REQUIRED",
      "open_event_count": 1,
      "latest_lab_observed_at": "2026-06-21T08:00:00Z"
    },
    {
      "id": 2,
      "patient_code": "P002",
      "display_name": "Synthetic Patient B",
      "is_synthetic": true,
      "current_severity": "NORMAL",
      "open_event_count": 0,
      "latest_lab_observed_at": "2026-06-21T08:00:00Z"
    }
  ],
  "total": 2
}
```

### Sorting Requirement

The backend should return patients in this order:

1. `HIGH_RISK`
2. `REVIEW_REQUIRED`
3. `NORMAL`

Patients with the same severity may be sorted by latest update time descending.

---

## 8.2 Get Patient Detail

### Request

```http
GET /api/patients/{patient_id}
```

### Path Parameters

| Name | Type | Required | Description |
|---|---|---:|---|
| `patient_id` | integer | yes | Internal patient ID |

### Success Response

Status: `200 OK`

```json
{
  "id": 1,
  "patient_code": "P001",
  "display_name": "Synthetic Patient A",
  "is_synthetic": true,
  "current_severity": "REVIEW_REQUIRED",
  "open_event_count": 1,
  "created_at": "2026-06-20T00:00:00Z"
}
```

### Error Response

Status: `404 Not Found`

```json
{
  "error": {
    "code": "PATIENT_NOT_FOUND",
    "message": "Patient 999 was not found."
  }
}
```

---

## 8.3 List Patient Laboratory Results

### Request

```http
GET /api/patients/{patient_id}/labs
```

### Success Response

Status: `200 OK`

```json
{
  "patient_id": 1,
  "items": [
    {
      "id": 1,
      "test_name": "creatinine",
      "value": 0.8,
      "unit": "mg/dL",
      "reference_min": 0.6,
      "reference_max": 1.2,
      "observed_at": "2026-06-20T08:00:00Z",
      "source_document": "synthetic_lab_report_20260620.csv"
    },
    {
      "id": 2,
      "test_name": "creatinine",
      "value": 1.3,
      "unit": "mg/dL",
      "reference_min": 0.6,
      "reference_max": 1.2,
      "observed_at": "2026-06-21T08:00:00Z",
      "source_document": "synthetic_lab_report_20260621.csv"
    }
  ],
  "total": 2
}
```

### Sorting Requirement

Laboratory results must be sorted by `observed_at` ascending unless the API explicitly documents another order.

---

## 8.4 List Patient Events

### Request

```http
GET /api/patients/{patient_id}/events
```

### Success Response

Status: `200 OK`

```json
{
  "patient_id": 1,
  "items": [
    {
      "id": 1,
      "event_type": "RAPID_LAB_CHANGE",
      "severity": "REVIEW_REQUIRED",
      "status": "OPEN",
      "title": "Creatinine rapid increase requires review",
      "description": "Prototype rule triggered: creatinine increased from 0.8 mg/dL to 1.3 mg/dL within 24 hours. Human review is required.",
      "rule_id": "RAPID_INCREASE",
      "created_at": "2026-06-21T08:00:01Z",
      "acknowledged_at": null,
      "resolved_at": null
    }
  ],
  "total": 1
}
```

---

# 9. Event APIs

## 9.1 Get Event Detail

### Request

```http
GET /api/events/{event_id}
```

### Success Response

Status: `200 OK`

```json
{
  "id": 1,
  "patient": {
    "id": 1,
    "patient_code": "P001",
    "display_name": "Synthetic Patient A",
    "is_synthetic": true
  },
  "event_type": "RAPID_LAB_CHANGE",
  "severity": "REVIEW_REQUIRED",
  "status": "OPEN",
  "title": "Creatinine rapid increase requires review",
  "description": "Prototype rule triggered: creatinine increased from 0.8 mg/dL to 1.3 mg/dL within 24 hours. Human review is required.",
  "rule_id": "RAPID_INCREASE",
  "created_at": "2026-06-21T08:00:01Z",
  "acknowledged_at": null,
  "resolved_at": null,
  "analysis": {
    "test_name": "creatinine",
    "previous_value": 0.8,
    "current_value": 1.3,
    "unit": "mg/dL",
    "previous_observed_at": "2026-06-20T08:00:00Z",
    "current_observed_at": "2026-06-21T08:00:00Z",
    "time_difference_hours": 24.0
  },
  "evidence": [
    {
      "evidence_link_id": 1,
      "relation_type": "PREVIOUS_VALUE",
      "lab_result": {
        "id": 1,
        "value": 0.8,
        "unit": "mg/dL",
        "observed_at": "2026-06-20T08:00:00Z",
        "source_document": "synthetic_lab_report_20260620.csv"
      }
    },
    {
      "evidence_link_id": 2,
      "relation_type": "CURRENT_VALUE",
      "lab_result": {
        "id": 2,
        "value": 1.3,
        "unit": "mg/dL",
        "observed_at": "2026-06-21T08:00:00Z",
        "source_document": "synthetic_lab_report_20260621.csv"
      }
    }
  ]
}
```

### Error Response

Status: `404 Not Found`

```json
{
  "error": {
    "code": "EVENT_NOT_FOUND",
    "message": "Event 999 was not found."
  }
}
```

---

## 9.2 Acknowledge Event

### Request

```http
POST /api/events/{event_id}/acknowledge
```

### Request Body

The body may be empty in Sprint 0.

```json
{}
```

Optional implementation:

```json
{
  "note": "Reviewed during prototype demo."
}
```

### Valid Transition

```text
OPEN → ACKNOWLEDGED
```

### Success Response

Status: `200 OK`

```json
{
  "id": 1,
  "status": "ACKNOWLEDGED",
  "acknowledged_at": "2026-06-21T09:00:00Z",
  "resolved_at": null
}
```

### Invalid Transition

If the event is already resolved:

Status: `409 Conflict`

```json
{
  "error": {
    "code": "INVALID_EVENT_TRANSITION",
    "message": "A resolved event cannot be acknowledged."
  }
}
```

### Idempotency

Acknowledging an already acknowledged event should not create duplicate records.

The backend may either:

- Return `200 OK` with the current state, or
- Return `409 Conflict`

Choose one behavior and document it in the implementation README. Returning `200 OK` is recommended for Sprint 0.

---

## 9.3 Resolve Event

### Request

```http
POST /api/events/{event_id}/resolve
```

### Request Body

```json
{
  "resolution_note": "Prototype event closed after human review."
}
```

`resolution_note` may be optional in Sprint 0, but the database design should allow it to be added later.

### Valid Transitions

```text
OPEN → RESOLVED
ACKNOWLEDGED → RESOLVED
```

For the demo workflow, `ACKNOWLEDGED → RESOLVED` is preferred.

### Success Response

Status: `200 OK`

```json
{
  "id": 1,
  "status": "RESOLVED",
  "acknowledged_at": "2026-06-21T09:00:00Z",
  "resolved_at": "2026-06-21T09:10:00Z"
}
```

### Invalid Transition

Status: `409 Conflict`

```json
{
  "error": {
    "code": "INVALID_EVENT_TRANSITION",
    "message": "The event is already resolved."
  }
}
```

---

# 10. Prototype Analysis API

## 10.1 Run Prototype Analysis

### Request

```http
POST /api/prototype/run-analysis
```

### Request Body

Sprint 0 may analyze all patients:

```json
{}
```

Optional patient-specific form:

```json
{
  "patient_id": 1
}
```

If patient-specific analysis is not implemented, reject unsupported fields with validation errors rather than silently ignoring them.

### Analysis Rule

Sprint 0 supports only:

```text
Rule ID: RAPID_INCREASE
Test: creatinine
Previous value: 0.8 mg/dL
Current value: 1.3 mg/dL
Maximum interval: 24 hours
```

This is a synthetic prototype rule and must not be presented as a validated clinical rule.

### Success Response

Status: `200 OK`

```json
{
  "analysis_run_id": "prototype-20260621T080001Z",
  "patients_analyzed": 3,
  "events_created": 1,
  "events_skipped_as_duplicates": 0,
  "insufficient_data_count": 1,
  "results": [
    {
      "patient_id": 1,
      "patient_code": "P001",
      "result": "EVENT_CREATED",
      "event_id": 1,
      "rule_id": "RAPID_INCREASE"
    },
    {
      "patient_id": 2,
      "patient_code": "P002",
      "result": "NO_TRIGGER",
      "event_id": null,
      "rule_id": "RAPID_INCREASE"
    },
    {
      "patient_id": 3,
      "patient_code": "P003",
      "result": "INSUFFICIENT_DATA",
      "event_id": null,
      "rule_id": "RAPID_INCREASE"
    }
  ]
}
```

### Duplicate Prevention

Running this endpoint multiple times with the same pair of laboratory results must not create duplicate events.

A duplicate may be identified by a unique combination such as:

```text
patient_id + rule_id + previous_lab_result_id + current_lab_result_id
```

### Repeated Analysis Response

Example:

```json
{
  "analysis_run_id": "prototype-20260621T081500Z",
  "patients_analyzed": 3,
  "events_created": 0,
  "events_skipped_as_duplicates": 1,
  "insufficient_data_count": 1,
  "results": [
    {
      "patient_id": 1,
      "patient_code": "P001",
      "result": "DUPLICATE_SKIPPED",
      "event_id": 1,
      "rule_id": "RAPID_INCREASE"
    }
  ]
}
```

---

# 11. Device State API

## 11.1 Get Device State

### Request

```http
GET /api/device-state
```

### Success Response — Warning

Status: `200 OK`

```json
{
  "connection": "SIMULATED",
  "adapter_mode": "simulated",
  "connection_status": "CONNECTED",
  "hardware_available": false,
  "fallback_active": false,
  "state": "WARNING",
  "led": "YELLOW_BLINKING",
  "buzzer": "SHORT_BEEP",
  "derived_from_event_ids": [1],
  "updated_at": "2026-06-21T08:00:01Z",
  "last_heartbeat_at": null,
  "last_command": null,
  "last_error": null,
  "protocol_version": "tracecare-device-v1"
}
```

### Success Response — Acknowledged

```json
{
  "connection": "SIMULATED",
  "adapter_mode": "simulated",
  "connection_status": "CONNECTED",
  "hardware_available": false,
  "fallback_active": false,
  "state": "ACKNOWLEDGED",
  "led": "YELLOW_SOLID",
  "buzzer": "OFF",
  "derived_from_event_ids": [1],
  "updated_at": "2026-06-21T09:00:00Z",
  "last_heartbeat_at": null,
  "last_command": null,
  "last_error": null,
  "protocol_version": "tracecare-device-v1"
}
```

### Success Response — Normal

```json
{
  "connection": "SIMULATED",
  "adapter_mode": "simulated",
  "connection_status": "CONNECTED",
  "hardware_available": false,
  "fallback_active": false,
  "state": "NORMAL",
  "led": "GREEN_SOLID",
  "buzzer": "OFF",
  "derived_from_event_ids": [],
  "updated_at": "2026-06-21T09:10:00Z",
  "last_heartbeat_at": null,
  "last_command": null,
  "last_error": null,
  "protocol_version": "tracecare-device-v1"
}
```

### Success Response — USB Serial Offline Fallback

```json
{
  "connection": "USB_SERIAL_OFFLINE",
  "adapter_mode": "usb_serial",
  "connection_status": "OFFLINE",
  "hardware_available": false,
  "fallback_active": true,
  "state": "WARNING",
  "led": "YELLOW_BLINKING",
  "buzzer": "SHORT_BEEP",
  "derived_from_event_ids": [1],
  "updated_at": "2026-06-21T08:00:01Z",
  "last_heartbeat_at": null,
  "last_command": "PING seq=1 protocol=tracecare-device-v1",
  "last_error": "DEVICE_TIMEOUT",
  "protocol_version": "tracecare-device-v1"
}
```

`fallback_active=true` means the hardware adapter is unavailable, but dashboard state and laptop visual/audio fallback remain available.

## 11.2 Device Health

```http
GET /api/device/health
```

```json
{
  "connection": "SIMULATED",
  "adapter_mode": "simulated",
  "connection_status": "CONNECTED",
  "hardware_available": false,
  "fallback_active": false,
  "last_heartbeat_at": null,
  "last_command": null,
  "last_error": null,
  "protocol_version": "tracecare-device-v1"
}
```

## 11.3 Reconnect Device

```http
POST /api/device/reconnect
```

The response shape is the same as `GET /api/device/health`. Reconnect is safe to repeat.

---

## 11.4 Device State Priority

When multiple events exist, use the highest active priority:

```text
OPEN HIGH_RISK
→ CRITICAL
→ RED_BLINKING
→ INTERMITTENT

OPEN REVIEW_REQUIRED
→ WARNING
→ YELLOW_BLINKING
→ SHORT_BEEP

ACKNOWLEDGED but not RESOLVED
→ ACKNOWLEDGED
→ YELLOW_SOLID
→ OFF

No unresolved events
→ NORMAL
→ GREEN_SOLID
→ OFF
```

Recommended priority order:

```text
CRITICAL > WARNING > ACKNOWLEDGED > NORMAL
```

---

# 12. Optional Seed Endpoint

A seed endpoint is not required if seeding is implemented through a CLI command or startup task.

If implemented, it must be development-only.

## 12.1 Seed Synthetic Data

```http
POST /api/development/seed
```

### Success Response

```json
{
  "patients_created": 3,
  "lab_results_created": 5,
  "duplicates_skipped": 0
}
```

Repeated execution must not create duplicate records.

Do not expose this endpoint in a production configuration.

---

# 13. CORS Requirements

For local development, the backend should allow the frontend origin configured through an environment variable.

Example:

```text
FRONTEND_ORIGIN=http://localhost:5173
```

Do not use unrestricted CORS in production-oriented configuration.

---

# 14. OpenAPI Documentation

FastAPI-generated documentation should be available at:

```text
/docs
```

Optional ReDoc endpoint:

```text
/redoc
```

Each route should include:

- Summary
- Description
- Response model
- Documented error responses
- Tags

Recommended tags:

```text
health
patients
labs
events
analysis
device
```

---

# 15. Required Tests

The backend test suite must verify at least:

1. `GET /health` returns `200`.
2. `GET /api/patients` returns all synthetic patients.
3. Unknown patient IDs return `404`.
4. P001 laboratory history is returned in chronological order.
5. Running analysis creates one `RAPID_INCREASE` event for P001.
6. Running analysis does not create events for P002.
7. Running analysis reports insufficient data for P003.
8. Re-running analysis does not create a duplicate event.
9. Event detail includes both evidence laboratory results.
10. Acknowledge changes `OPEN` to `ACKNOWLEDGED`.
11. Resolve changes the event to `RESOLVED`.
12. Unknown event IDs return `404`.
13. Invalid event transitions return a documented error.
14. Device state changes according to event status.
15. After all events are resolved, device state returns to `NORMAL`.

---

# 16. Sprint 0 Acceptance Criteria

The API is accepted when:

- All documented endpoints are implemented.
- The OpenAPI documentation loads correctly.
- Synthetic seed data can be created repeatedly without duplicates.
- P001 triggers one traceable event.
- P002 and P003 do not create false events.
- Event evidence includes source documents and timestamps.
- Acknowledge and resolve operations persist correctly.
- Device state reflects the current event lifecycle.
- All automated backend tests pass.
- No external AI or medical data service is called.

---

# 17. Safety Statement

```text
TraceCare AI is a competition prototype and is not a medical device.
It must not be used for diagnosis or treatment decisions.
All patient data included in Sprint 0 is synthetic.
The RAPID_INCREASE rule is a synthetic demonstration rule and is not a validated clinical rule.
```

---

# 18. Sprint 1 API Addendum

Sprint 1 extends the Sprint 0 API without removing or renaming existing fields.

## 18.1 New Enumerations

Additional event type:

```text
CONTRADICTION
```

Additional rule ID:

```text
ALLERGY_CONTRADICTION
```

Additional typed evidence relation types:

```text
ASSERTED_FACT
DENIED_FACT
SOURCE_DOCUMENT
```

## 18.2 Documents and Facts

```http
GET /api/patients/{patient_id}/documents
GET /api/documents/{document_id}
GET /api/patients/{patient_id}/facts
```

Document responses include `id`, `patient_id`, `document_type`, `title`, `source_document`, `authored_at`, `created_at`, and `is_synthetic`.

Fact responses include source traceability fields: `source_section`, `source_line`, `source_start_char`, `source_end_char`, and `observed_at`.

Unknown patients return `PATIENT_NOT_FOUND`. Unknown documents return `DOCUMENT_NOT_FOUND`.

## 18.3 Contradiction Analysis

```http
POST /api/prototype/run-contradiction-analysis
```

Runs deterministic fixed-format allergy contradiction detection for all synthetic patients.

Success response:

```json
{
  "analysis_run_id": "prototype-contradiction-20260701T120000Z",
  "patients_analyzed": 3,
  "events_created": 1,
  "events_skipped_as_duplicates": 0,
  "insufficient_data_count": 1,
  "results": [
    {
      "patient_id": 1,
      "patient_code": "P001",
      "result": "EVENT_CREATED",
      "event_id": 2,
      "rule_id": "ALLERGY_CONTRADICTION",
      "subject": "penicillin"
    }
  ]
}
```

## 18.4 Event Detail Extension

`GET /api/events/{event_id}` now includes a backward-compatible additional field:

```json
{
  "document_evidence": [
    {
      "event_evidence_id": 1,
      "target_type": "clinical_fact",
      "target_id": 1,
      "relation_type": "ASSERTED_FACT",
      "clinical_fact": {
        "id": 1,
        "fact_type": "ALLERGY_STATEMENT",
        "subject": "penicillin",
        "polarity": "PRESENT",
        "value": "Allergy: Penicillin",
        "status": "ACTIVE",
        "source_section": "Allergies",
        "source_line": 4,
        "source_start_char": 10,
        "source_end_char": 20,
        "observed_at": "2026-06-21T09:00:00Z",
        "document": {
          "id": 1,
          "document_type": "ADMISSION_NOTE",
          "title": "Synthetic admission note",
          "source_document": "synthetic_admission_note_p001_20260621.txt",
          "authored_at": "2026-06-21T09:00:00Z",
          "is_synthetic": true
        }
      },
      "clinical_document": null
    }
  ]
}
```

Sprint 0 lab evidence remains in the existing `evidence` field.

## 18.5 Evidence Graph

```http
GET /api/patients/{patient_id}/evidence-graph
GET /api/events/{event_id}/evidence-graph
```

Response shape:

```json
{
  "scope": "patient",
  "nodes": [
    {"id": "patient:1", "type": "patient", "label": "P001", "metadata": {"is_synthetic": true}}
  ],
  "edges": [
    {"id": "patient:1->document:1:HAS_DOCUMENT", "source": "patient:1", "target": "document:1", "relation": "HAS_DOCUMENT", "metadata": {}}
  ]
}
```

Graph direction is source-to-derived-record, for example `document -> fact` and `fact -> event`.

---

# 19. Sprint 2 API Addendum

Sprint 2 extends Sprint 0 and Sprint 1 without removing or renaming existing fields.

## 19.1 Event Lifecycle Fields

Event list, event detail, and lifecycle action responses may include:

```json
{
  "deferred_at": null,
  "deferred_until": null,
  "escalated_at": null,
  "escalation_reason": null
}
```

`DEFERRED` is an unresolved event status. Existing `OPEN`, `ACKNOWLEDGED`, and `RESOLVED` statuses remain valid.

## 19.2 Defer Event

```http
POST /api/events/{event_id}/defer
```

Optional request body:

```json
{
  "reason": "Prototype reviewer deferred follow-up",
  "defer_until": "2026-06-21T13:00:00Z",
  "actor_label": "prototype-reviewer"
}
```

Success response has the same lifecycle event shape as acknowledge and resolve. Deferred events remain unresolved and visible.

## 19.3 Event Actions

```http
GET /api/events/{event_id}/actions
```

Success response:

```json
{
  "event_id": 1,
  "items": [
    {
      "id": 1,
      "event_id": 1,
      "patient_id": 1,
      "action_type": "DEFER",
      "actor_label": "prototype-reviewer",
      "note": "Prototype reviewer deferred follow-up",
      "created_at": "2026-06-21T09:00:00Z"
    }
  ],
  "total": 1
}
```

`GET /api/events/{event_id}` also includes a backward-compatible additive `action_history` array.

## 19.4 Patient Risk

```http
GET /api/patients/{patient_id}/risk
```

Success response:

```json
{
  "patient_id": 1,
  "patient_code": "P001",
  "risk_state": "HIGH_RISK",
  "risk_reasons": [
    {
      "code": "MULTIPLE_EVENT_TYPES",
      "message": "Multiple unresolved prototype event types are present for the same synthetic patient.",
      "event_ids": [1, 2]
    }
  ],
  "unresolved_event_count": 2,
  "oldest_unresolved_event_at": "2026-06-21T08:00:01Z",
  "driver_event_ids": [1, 2]
}
```

`GET /api/patients` includes additive summary fields:

```json
{
  "risk_reasons": ["MULTIPLE_EVENT_TYPES"],
  "oldest_unresolved_event_at": "2026-06-21T08:00:01Z",
  "driver_event_ids": [1, 2]
}
```

## 19.5 Run Risk Evaluation

```http
POST /api/prototype/run-risk-evaluation
```

Optional request body:

```json
{
  "evaluated_at": "2026-06-21T11:00:00Z"
}
```

Success response:

```json
{
  "evaluation_run_id": "prototype-risk-20260621T110000Z",
  "evaluated_at": "2026-06-21T11:00:00Z",
  "patients_evaluated": 3,
  "events_escalated": 1,
  "results": []
}
```

Risk evaluation is deterministic. It escalates open events only when the documented timeout rule is met and records `AUTO_ESCALATE` once per event.

---

# 20. Sprint 3 API Addendum

Sprint 3 adds evidence-first local summary APIs. Existing Sprint 0 through Sprint 2 fields and endpoints remain unchanged.

## 20.1 Create Patient Summary

```http
POST /api/patients/{patient_id}/summaries/patient
POST /api/patients/{patient_id}/summaries/handoff
```

Optional request body:

```json
{
  "prefer_llm": true
}
```

When `LLM_MODE=disabled`, the backend returns a deterministic fallback summary. If evidence is insufficient, it abstains.

Success response:

```json
{
  "id": "summary-uuid",
  "patient_id": 1,
  "patient_code": "P001",
  "summary_kind": "patient",
  "status": "FALLBACK",
  "validation_status": "PASSED",
  "adapter_mode": "deterministic-fallback",
  "model_name": null,
  "local_only": true,
  "text": "Validated summary text.",
  "sentences": [
    {
      "index": 0,
      "text": "P001 is a synthetic TraceCare AI patient in this prototype.",
      "evidence_ids": ["patient:1"]
    }
  ],
  "evidence_package": {
    "package_id": "patient:1:patient",
    "patient_id": 1,
    "patient_code": "P001",
    "summary_kind": "patient",
    "evidence_items": [],
    "sufficient": true,
    "insufficiency_reason": null
  },
  "validation_errors": [],
  "abstention_reason": null,
  "created_at": "2026-07-02T00:00:00Z"
}
```

Possible `status` values:

```text
GENERATED
FALLBACK
ABSTAINED
REJECTED
```

## 20.2 Retrieve Summary

```http
GET /api/summaries/{summary_id}
GET /api/summaries/{summary_id}/evidence
```

Unknown summary IDs return `SUMMARY_NOT_FOUND`.

## 20.3 Validation Requirements

- Each sentence must cite evidence IDs.
- Unknown citations are rejected.
- Numeric values must match cited evidence.
- Diagnosis or treatment language is rejected.
- LLM output must not calculate risk; risk context comes from `GET /api/patients/{patient_id}/risk` and the Evidence Package.
