export interface EvidenceItem {
  id: string;
  type: string;
  label: string;
  text: string;
  numeric_values: string[];
  metadata: Record<string, unknown>;
}

export interface EvidencePackage {
  package_id: string;
  patient_id: number;
  patient_code: string;
  summary_kind: "patient" | "handoff" | string;
  evidence_items: EvidenceItem[];
  sufficient: boolean;
  insufficiency_reason: string | null;
}

export interface SummarySentence {
  index: number;
  text: string;
  evidence_ids: string[];
}

export interface SummaryResponse {
  id: string;
  patient_id: number;
  patient_code: string;
  summary_kind: "patient" | "handoff" | string;
  status: "GENERATED" | "FALLBACK" | "ABSTAINED" | "REJECTED" | string;
  validation_status: "PASSED" | "FAILED" | "ABSTAINED" | string;
  adapter_mode: string;
  model_name: string | null;
  local_only: boolean;
  text: string;
  sentences: SummarySentence[];
  evidence_package: EvidencePackage;
  validation_errors: string[];
  abstention_reason: string | null;
  created_at: string;
}
