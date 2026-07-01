import { apiGet } from "./client";
import type { LabListResponse } from "../types/lab";
import type { EventListResponse } from "../types/event";
import type { PatientDetail, PatientListResponse } from "../types/patient";

export const fetchPatients = () => apiGet<PatientListResponse>("/patients");
export const fetchPatient = (patientId: number) => apiGet<PatientDetail>(`/patients/${patientId}`);
export const fetchPatientLabs = (patientId: number) => apiGet<LabListResponse>(`/patients/${patientId}/labs`);
export const fetchPatientEvents = (patientId: number) =>
  apiGet<EventListResponse>(`/patients/${patientId}/events`);
