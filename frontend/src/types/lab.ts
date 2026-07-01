export interface LabResult {
  id: number;
  test_name: string;
  value: number;
  unit: string;
  reference_min: number;
  reference_max: number;
  observed_at: string;
  source_document: string;
}

export interface LabListResponse {
  patient_id: number;
  items: LabResult[];
  total: number;
}
