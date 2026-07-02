import { apiGet, apiPost } from "./client";
import type { ClinicalEvent, DeferEventRequest, EventActionsResponse, EventDetail } from "../types/event";

export const fetchEvent = (eventId: number) => apiGet<EventDetail>(`/events/${eventId}`);
export const fetchEventActions = (eventId: number) =>
  apiGet<EventActionsResponse>(`/events/${eventId}/actions`);
export const acknowledgeEvent = (eventId: number) =>
  apiPost<
    Pick<
      ClinicalEvent,
      | "id"
      | "status"
      | "acknowledged_at"
      | "deferred_at"
      | "deferred_until"
      | "escalated_at"
      | "escalation_reason"
      | "resolved_at"
    >
  >(
    `/events/${eventId}/acknowledge`
  );
export const deferEvent = (eventId: number, payload: DeferEventRequest = {}) =>
  apiPost<
    Pick<
      ClinicalEvent,
      | "id"
      | "status"
      | "acknowledged_at"
      | "deferred_at"
      | "deferred_until"
      | "escalated_at"
      | "escalation_reason"
      | "resolved_at"
    >
  >(`/events/${eventId}/defer`, payload);
export const resolveEvent = (eventId: number) =>
  apiPost<
    Pick<
      ClinicalEvent,
      | "id"
      | "status"
      | "acknowledged_at"
      | "deferred_at"
      | "deferred_until"
      | "escalated_at"
      | "escalation_reason"
      | "resolved_at"
    >
  >(
    `/events/${eventId}/resolve`
  );
