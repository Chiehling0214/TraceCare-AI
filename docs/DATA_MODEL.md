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
