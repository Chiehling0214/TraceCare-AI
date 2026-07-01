export interface ClinicalDocument {
  id: number;
  patient_id: number;
  document_type: string;
  title: string;
  source_document: string;
  authored_at: string;
  created_at: string;
  is_synthetic: boolean;
}

export interface ClinicalDocumentListResponse {
  patient_id: number;
  items: ClinicalDocument[];
  total: number;
}

export interface ClinicalFact {
  id: number;
  patient_id: number;
  document_id: number;
  fact_type: string;
  subject: string;
  polarity: "PRESENT" | "NEGATED" | string;
  value: string;
  status: string;
  source_section: string;
  source_line: number;
  source_start_char: number;
  source_end_char: number;
  observed_at: string;
  created_at: string;
}

export interface ClinicalFactListResponse {
  patient_id: number;
  items: ClinicalFact[];
  total: number;
}
