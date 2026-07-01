# Sprint 0 Data Model

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