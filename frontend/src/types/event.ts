export type EventStatus = "OPEN" | "ACKNOWLEDGED" | "DEFERRED" | "RESOLVED";

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
  deferred_at: string | null;
  deferred_until: string | null;
  escalated_at: string | null;
  escalation_reason: string | null;
  resolved_at: string | null;
}

export interface EventAction {
  id: number;
  event_id: number;
  patient_id: number;
  action_type: "ACKNOWLEDGE" | "DEFER" | "RESOLVE" | "AUTO_ESCALATE" | string;
  actor_label: string;
  note: string | null;
  created_at: string;
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
  document_evidence: Array<{
    event_evidence_id: number;
    target_type: string;
    target_id: number;
    relation_type: string;
    clinical_fact: {
      id: number;
      fact_type: string;
      subject: string;
      polarity: string;
      value: string;
      status: string;
      source_section: string;
      source_line: number;
      source_start_char: number;
      source_end_char: number;
      observed_at: string;
      document: EvidenceDocument;
    } | null;
    clinical_document: EvidenceDocument | null;
  }>;
  action_history: EventAction[];
}

export interface DeferEventRequest {
  reason?: string;
  defer_until?: string | null;
  actor_label?: string;
}

export interface EventActionsResponse {
  event_id: number;
  items: EventAction[];
  total: number;
}

export interface AnalysisRunResponse {
  analysis_run_id: string;
  patients_analyzed: number;
  events_created: number;
  events_skipped_as_duplicates: number;
  insufficient_data_count: number;
  results: Array<{
    patient_id: number;
    patient_code: string;
    result: string;
    event_id: number | null;
    rule_id: string;
  }>;
}

export interface ContradictionAnalysisRunResponse extends AnalysisRunResponse {
  results: Array<{
    patient_id: number;
    patient_code: string;
    result: string;
    event_id: number | null;
    rule_id: string;
    subject: string | null;
  }>;
}

export interface RiskEvaluationResponse {
  evaluation_run_id: string;
  patients_evaluated: number;
  events_escalated: number;
  evaluated_at: string;
  results: Array<{
    patient_id: number;
    patient_code: string;
    risk_state: "NORMAL" | "REVIEW_REQUIRED" | "HIGH_RISK";
    unresolved_event_count: number;
    oldest_unresolved_event_at: string | null;
    risk_reasons: Array<{
      code: string;
      message: string;
      event_ids: number[];
    }>;
    driver_event_ids: number[];
  }>;
}

interface EvidenceDocument {
  id: number;
  document_type: string;
  title: string;
  source_document: string;
  authored_at: string;
  is_synthetic: boolean;
}
