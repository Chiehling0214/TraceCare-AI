export type Severity = "NORMAL" | "REVIEW_REQUIRED" | "HIGH_RISK";

export interface PatientSummary {
  id: number;
  patient_code: string;
  display_name: string;
  is_synthetic: boolean;
  current_severity: Severity;
  open_event_count: number;
  latest_lab_observed_at: string | null;
  risk_reasons: string[];
  oldest_unresolved_event_at: string | null;
  driver_event_ids: number[];
}

export interface PatientDetail extends PatientSummary {
  created_at: string;
}

export interface PatientListResponse {
  items: PatientSummary[];
  total: number;
}
