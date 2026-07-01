import { apiGet } from "./client";
import type { EvidenceGraph } from "../types/graph";

export const fetchPatientEvidenceGraph = (patientId: number) =>
  apiGet<EvidenceGraph>(`/patients/${patientId}/evidence-graph`);

export const fetchEventEvidenceGraph = (eventId: number) =>
  apiGet<EvidenceGraph>(`/events/${eventId}/evidence-graph`);
