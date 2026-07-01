export type EventStatus = "OPEN" | "ACKNOWLEDGED" | "RESOLVED";

export interface ClinicalEvent {
  id: number;
  event_type: string;
  severity: string;
  status: EventStatus;
  title: string;
  description: string;
  rule_id: string;
  created_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
}

export interface EventListResponse {
  patient_id: number;
  items: ClinicalEvent[];
  total: number;
}

export interface EventDetail extends ClinicalEvent {
  patient: {
    id: number;
    patient_code: string;
    display_name: string;
    is_synthetic: boolean;
  };
  analysis: {
    test_name: string;
    previous_value: number;
    current_value: number;
    unit: string;
    previous_observed_at: string;
    current_observed_at: string;
    time_difference_hours: number;
  } | null;
  evidence: Array<{
    evidence_link_id: number;
    relation_type: string;
    lab_result: {
      id: number;
      test_name: string;
      value: number;
      unit: string;
      observed_at: string;
      source_document: string;
    };
  }>;
}

export interface AnalysisRunResponse {
  analysis_run_id: string;
  patients_analyzed: number;
  events_created: number;
  events_skipped_as_duplicates: number;
  insufficient_data_count: number;
}
