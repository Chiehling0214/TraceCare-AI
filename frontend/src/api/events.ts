import { apiGet, apiPost } from "./client";
import type { ClinicalEvent, EventDetail } from "../types/event";

export const fetchEvent = (eventId: number) => apiGet<EventDetail>(`/events/${eventId}`);
export const acknowledgeEvent = (eventId: number) =>
  apiPost<Pick<ClinicalEvent, "id" | "status" | "acknowledged_at" | "resolved_at">>(
    `/events/${eventId}/acknowledge`
  );
export const resolveEvent = (eventId: number) =>
  apiPost<Pick<ClinicalEvent, "id" | "status" | "acknowledged_at" | "resolved_at">>(
    `/events/${eventId}/resolve`
  );
