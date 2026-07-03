import { apiGet } from "./client";
import { apiPost } from "./client";
import type { DeviceHealth, DeviceState } from "../types/device";

export const fetchDeviceState = () => apiGet<DeviceState>("/device-state");
export const fetchDeviceHealth = () => apiGet<DeviceHealth>("/device/health");
export const reconnectDevice = () => apiPost<DeviceHealth>("/device/reconnect");
