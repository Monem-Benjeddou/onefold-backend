"use client";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data: unknown,
  ) {
    super(message);
  }

  /** Field errors from a DRF 400 (`{"field": ["message"]}`), first message per field. */
  get fields(): Record<string, string> {
    const out: Record<string, string> = {};
    if (this.data && typeof this.data === "object") {
      for (const [key, value] of Object.entries(this.data as Record<string, unknown>)) {
        if (Array.isArray(value) && typeof value[0] === "string") out[key] = value[0];
      }
    }
    return out;
  }

  get requestId(): string | null {
    const data = this.data as { request_id?: string } | null;
    return data?.request_id ?? null;
  }
}

/** Turn a DRF error body into one human sentence. */
export function errorMessage(data: unknown, fallback = "Something went wrong. Try again."): string {
  if (!data || typeof data !== "object") return fallback;
  const body = data as Record<string, unknown>;
  if (typeof body.detail === "string") return body.detail;
  for (const [key, value] of Object.entries(body)) {
    if (key === "code" || key === "request_id") continue;
    if (Array.isArray(value) && typeof value[0] === "string") return value[0];
    if (typeof value === "string") return value;
  }
  return fallback;
}

let refreshing: Promise<boolean> | null = null;

/** Renew the session once, shared by every call that hit a 401 at the same time. */
function refreshSession() {
  refreshing ??= fetch("/api/auth/refresh", { method: "POST" })
    .then((response) => response.ok)
    .catch(() => false)
    .finally(() => {
      setTimeout(() => (refreshing = null), 0);
    });
  return refreshing;
}

/** The session can't be renewed: sign in again, then come back here. */
function onSignedOut() {
  window.location.href = `/login?expired=1&next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
}

/** Call the API from the browser through the same-origin proxy (cookies carry the session). */
export async function call<T>(
  path: string,
  init: { method?: string; body?: unknown; headers?: Record<string, string> } = {},
): Promise<T> {
  const send = () =>
    fetch(`/api/proxy${path}`, {
      method: init.method ?? "GET",
      headers: { "Content-Type": "application/json", ...init.headers },
      body: init.body === undefined ? undefined : JSON.stringify(init.body),
    });

  let response: Response;
  try {
    response = await send();
    // The proxy already renews expired access tokens; this covers a race with
    // another tab that rotated the refresh token first.
    if (response.status === 401 && (await refreshSession())) response = await send();
  } catch {
    throw new ApiError("Can't reach Onefold. Check your connection and try again.", 0, null);
  }
  if (response.status === 401) {
    onSignedOut();
    throw new ApiError("Your session ended. Sign in again to continue.", 401, null);
  }
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(errorMessage(data), response.status, data);
  return data as T;
}
