const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export class ApiRequestError extends Error {
  code: string;

  constructor(message: string, code = "API_REQUEST_FAILED") {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body)
  });
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init.headers ?? {}) }
    });
  } catch {
    throw new ApiRequestError("Backend service is unavailable. Check Docker Compose or the local API process.", "BACKEND_UNAVAILABLE");
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message =
      payload?.detail?.error?.message ?? payload?.error?.message ?? `Request failed with ${response.status}`;
    const code = payload?.detail?.error?.code ?? payload?.error?.code ?? "API_REQUEST_FAILED";
    throw new ApiRequestError(message, code);
  }
  return response.json() as Promise<T>;
}
