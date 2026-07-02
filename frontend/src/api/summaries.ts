import { apiPost } from "./client";
import type { SummaryResponse } from "../types/summary";

export const requestPatientSummary = (patientId: number) =>
  apiPost<SummaryResponse>(`/patients/${patientId}/summaries/patient`);

export const requestHandoffSummary = (patientId: number) =>
  apiPost<SummaryResponse>(`/patients/${patientId}/summaries/handoff`);
