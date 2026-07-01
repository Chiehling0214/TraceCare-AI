export interface DeviceState {
  connection: "SIMULATED";
  state: "NORMAL" | "WARNING" | "CRITICAL" | "ACKNOWLEDGED";
  led: string;
  buzzer: string;
  derived_from_event_ids: number[];
  updated_at: string;
}
