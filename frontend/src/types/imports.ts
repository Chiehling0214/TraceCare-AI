export interface ImportErrorItem {
  row: number | null;
  field: string | null;
  code: string;
  message: string;
}

export interface ImportPreviewRow {
  row: number;
  action: "CREATE" | "DUPLICATE_SKIP";
  patient_code: string | null;
  source_position: string;
  data: Record<string, unknown>;
}

export interface ImportPreviewResponse {
  import_kind: "labs" | "documents";
  schema_version: string;
  source_filename: string;
  valid: boolean;
  rows_received: number;
  rows_valid: number;
  duplicates_detected: number;
  errors: ImportErrorItem[];
  preview_rows: ImportPreviewRow[];
}

export interface ImportCommitResponse extends ImportPreviewResponse {
  import_id: number | null;
  committed: boolean;
  records_created: number;
  duplicates_skipped: number;
}

export interface DemoActionResponse {
  status: string;
  patients_deleted: number;
  patients_created: number;
  lab_results_created: number;
  clinical_documents_created: number;
  clinical_facts_created: number;
  events_created: number;
  events_escalated: number;
  duplicates_skipped: number;
  created_at: string | null;
}
