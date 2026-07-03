export interface DeviceState {
  connection: string;
  adapter_mode: "simulated" | "usb_serial" | string;
  connection_status: "CONNECTED" | "DISCONNECTED" | "RECONNECTING" | "OFFLINE" | string;
  hardware_available: boolean;
  fallback_active: boolean;
  state: "NORMAL" | "WARNING" | "CRITICAL" | "ACKNOWLEDGED";
  led: string;
  buzzer: string;
  derived_from_event_ids: number[];
  updated_at: string;
  last_heartbeat_at: string | null;
  last_command: string | null;
  last_error: string | null;
  protocol_version: string;
}

export type DeviceHealth = Omit<DeviceState, "state" | "led" | "buzzer" | "derived_from_event_ids" | "updated_at">;
