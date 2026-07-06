# TraceCare AI Sprint 5 Import Formats

Sprint 5 import is fixed-schema and synthetic-only. Do not import real patient data, real medical records, or identifiable information.

## Lab CSV

Schema version: `tracecare-labs-csv-v1`

Required columns:

```csv
patient_code,display_name,test_name,value,unit,reference_min,reference_max,observed_at,source_document
```

Rules:

- `patient_code` must be a synthetic code beginning with `P`.
- `test_name` must be `creatinine`.
- `unit` must be `mg/dL`.
- `value`, `reference_min`, and `reference_max` must be numeric.
- `observed_at` must be ISO-8601 datetime.
- `source_document` is preserved on `LabResult.source_document`.
- Duplicate rows inside one file are invalid.
- Rows already present in the database are skipped with an explicit duplicate report.

## Clinical Document JSON

Schema version: `tracecare-documents-json-v1`

Top-level shape:

```json
{
  "schema_version": "tracecare-documents-json-v1",
  "documents": []
}
```

Each document requires:

- `patient_code`
- `display_name`
- `document_type`
- `title`
- `source_document`
- `authored_at`
- `facts`

Each fact requires:

- `fact_type`
- `subject`
- `polarity`
- `value`
- `status`
- `source_section`
- `source_line`
- `source_start_char`
- `source_end_char`
- `observed_at`

Supported fact rules:

- `fact_type`: `ALLERGY_STATEMENT`
- `polarity`: `PRESENT` or `NEGATED`
- `status`: `ACTIVE`, `DENIED`, or `UNKNOWN`
- `source_end_char` must be greater than `source_start_char`

## Demo Data

Repository fixtures:

- `backend/app/seed/demo_labs.csv`
- `backend/app/seed/demo_documents.json`

Use the Demo Data page or API endpoints to preview before commit.
