# TraceCare AI Data Model

## Sprint 0 Data Model

## Patient

| Field | Type | Required | Description |
|---|---|---:|---|
| id | integer | yes | Internal primary key |
| patient_code | string | yes | Synthetic patient identifier |
| display_name | string | yes | Synthetic display name |
| created_at | datetime | yes | Creation timestamp |

## LabResult

| Field | Type | Required | Description |
|---|---|---:|---|
| id | integer | yes | Internal primary key |
| patient_id | integer | yes | Patient foreign key |
| test_name | string | yes | Sprint 0 supports creatinine |
| value | decimal | yes | Numeric result |
| unit | string | yes | mg/dL |
| reference_min | decimal | yes | Synthetic reference minimum |
| reference_max | decimal | yes | Synthetic reference maximum |
| observed_at | datetime | yes | Observation time |
| source_document | string | yes | Synthetic source filename |

## ClinicalEvent

| Field | Type |
|---|---|
| id | integer |
| patient_id | integer |
| event_type | enum |
| severity | enum |
| status | enum |
| title | string |
| description | text |
| rule_id | string |
| created_at | datetime |
| acknowledged_at | datetime, nullable |
| deferred_at | datetime, nullable |
| deferred_until | datetime, nullable |
| escalated_at | datetime, nullable |
| escalation_reason | string, nullable |
| resolved_at | datetime, nullable |

## EvidenceLink

| Field | Type |
|---|---|
| id | integer |
| event_id | integer |
| lab_result_id | integer |
| relation_type | enum |

## Sprint 1 Additive Data Model

Sprint 1 keeps the Sprint 0 tables intact and adds new tables through SQLAlchemy `create_all`.

## ClinicalDocument

| Field | Type | Required | Description |
|---|---|---:|---|
| id | integer | yes | Internal primary key |
| patient_id | integer | yes | Patient foreign key |
| document_type | string | yes | Fixed synthetic document type |
| title | string | yes | Human-readable synthetic document title |
| source_document | string | yes | Synthetic source filename |
| authored_at | datetime | yes | Document authored time |
| created_at | datetime | yes | Creation timestamp |
| is_synthetic | boolean | yes | Always true for included seed data |

## Sprint 2 Additive Data Model

Sprint 2 keeps Sprint 0 and Sprint 1 data intact. It adds lifecycle metadata to `ClinicalEvent` and a persisted action/audit table.

## EventAction

| Field | Type | Required | Description |
|---|---|---:|---|
| id | integer | yes | Internal primary key |
| event_id | integer | yes | ClinicalEvent foreign key |
| patient_id | integer | yes | Patient foreign key |
| action_type | string | yes | `ACKNOWLEDGE`, `DEFER`, `RESOLVE`, or `AUTO_ESCALATE` |
| actor_label | string | yes | Synthetic actor label such as `prototype-reviewer` or `prototype-system` |
| note | text | no | Synthetic reason or audit note |
| created_at | datetime | yes | Action timestamp |

## Sprint 2 Event Statuses

`ClinicalEvent.status` supports:

| Status | Meaning |
|---|---|
| OPEN | Newly created unresolved event |
| ACKNOWLEDGED | Reviewed but not resolved |
| DEFERRED | Deferred and still unresolved |
| RESOLVED | Closed event |

`OPEN`, `ACKNOWLEDGED`, and `RESOLVED` remain backward-compatible with Sprint 0 and Sprint 1.

## ClinicalFact

| Field | Type | Required | Description |
|---|---|---:|---|
| id | integer | yes | Internal primary key |
| patient_id | integer | yes | Patient foreign key |
| document_id | integer | yes | ClinicalDocument foreign key |
| fact_type | string | yes | Sprint 1 supports `ALLERGY_STATEMENT` |
| subject | string | yes | Synthetic allergen or allergy subject |
| polarity | string | yes | `PRESENT` or `NEGATED` |
| value | string | yes | Fixed-format extracted statement |
| status | string | yes | `ACTIVE`, `DENIED`, or `UNKNOWN` |
| source_section | string | yes | Source section label |
| source_line | integer | yes | Source line number |
| source_start_char | integer | yes | Character start offset |
| source_end_char | integer | yes | Character end offset |
| observed_at | datetime | yes | Fact observation time |
| created_at | datetime | yes | Creation timestamp |

## EventEvidence

| Field | Type | Required | Description |
|---|---|---:|---|
| id | integer | yes | Internal primary key |
| event_id | integer | yes | ClinicalEvent foreign key |
| target_type | string | yes | `clinical_fact` or `clinical_document` |
| target_id | integer | yes | Target record ID |
| relation_type | string | yes | `ASSERTED_FACT`, `DENIED_FACT`, `SUPPORTS`, or `SOURCE_DOCUMENT` |
| created_at | datetime | yes | Creation timestamp |

## Sprint 3 Additive Data Model

Sprint 3 keeps Sprint 0 through Sprint 2 tables intact and adds optional summary persistence.

## SummaryRecord

| Field | Type | Required | Description |
|---|---|---:|---|
| id | string | yes | UUID summary identifier |
| patient_id | integer | yes | Patient foreign key |
| summary_kind | string | yes | `patient` or `handoff` |
| status | string | yes | `GENERATED`, `FALLBACK`, `ABSTAINED`, or `REJECTED` |
| validation_status | string | yes | `PASSED`, `FAILED`, or `ABSTAINED` |
| adapter_mode | string | yes | `disabled`, `deterministic-fallback`, `fake-test`, or local backend name |
| model_name | string | no | Local model name when used |
| local_only | string | yes | Stored as `true` for Sprint 3 |
| text | text | yes | Validated summary text, empty for abstention/rejection |
| sentences_json | text | yes | Sentence-level text and evidence ID mapping |
| evidence_package_json | text | yes | Evidence package snapshot used for validation |
| validation_errors_json | text | yes | Validation error codes |
| abstention_reason | text | no | Reason for abstention or rejection |
| created_at | datetime | yes | Summary creation timestamp |

## Sprint 4 Device State

Sprint 4 does not add a persistence table. Device state and health are transient backend adapter outputs derived from existing clinical event lifecycle/risk state and optional USB Serial adapter status.

Returned transient fields include:

| Field | Type | Notes |
|---|---|---|
| adapter_mode | string | `simulated` or `usb_serial` |
| connection_status | string | `CONNECTED`, `RECONNECTING`, `OFFLINE`, or adapter-specific status |
| hardware_available | boolean | True only when physical adapter heartbeat or command succeeds |
| fallback_active | boolean | True when dashboard/laptop fallback is active |
| last_heartbeat_at | datetime, nullable | Last successful heartbeat |
| last_command | string, nullable | Last sanitized protocol command |
| last_error | string, nullable | Sanitized device error code |
| protocol_version | string | `tracecare-device-v1` |
