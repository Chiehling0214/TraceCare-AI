import { apiGet } from "./client";
import type { DeviceState } from "../types/device";

export const fetchDeviceState = () => apiGet<DeviceState>("/device-state");
