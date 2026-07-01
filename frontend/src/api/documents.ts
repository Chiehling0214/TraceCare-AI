import { apiGet } from "./client";
import type { ClinicalDocument, ClinicalDocumentListResponse, ClinicalFactListResponse } from "../types/document";

export const fetchPatientDocuments = (patientId: number) =>
  apiGet<ClinicalDocumentListResponse>(`/patients/${patientId}/documents`);

export const fetchDocument = (documentId: number) => apiGet<ClinicalDocument>(`/documents/${documentId}`);

export const fetchPatientFacts = (patientId: number) =>
  apiGet<ClinicalFactListResponse>(`/patients/${patientId}/facts`);
