import "server-only";

import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";
import { cache } from "react";

import { ACCESS_COOKIE, BACKEND_URL, REFRESH_COOKIE } from "./session";
import type { AuthConfig, Workspace } from "./types";

export class ApiFailure extends Error {
  constructor(
    public path: string,
    public status: number,
    public requestId: string | null,
  ) {
    super(
      status >= 500 || status === 0
        ? "Onefold's API had a problem answering. It's on us, not you."
        : `The API refused ${path} (${status}).`,
    );
  }
}

/**
 * Fetch from the API inside a Server Component, as the signed-in builder.
 *
 * The proxy (src/proxy.ts) renews expiring tokens before pages render, so a
 * 401 here means the session is really over: go to the login page and come
 * back to `here` afterwards.
 */
export async function api<T>(path: string, here?: string): Promise<T | null> {
  const jar = await cookies();
  const access = jar.get(ACCESS_COOKIE)?.value;
  const back = here ?? (await currentPath());
  if (!access) bounce(back, jar.has(REFRESH_COOKIE));

  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}/api/v1${path}`, {
      headers: { Authorization: `Bearer ${access}` },
      cache: "no-store",
    });
  } catch {
    throw new ApiFailure(path, 0, null);
  }
  if (response.status === 401) bounce(back, jar.has(REFRESH_COOKIE));
  if (response.status === 404) return null;
  if (!response.ok) throw new ApiFailure(path, response.status, response.headers.get("x-request-id"));
  return (await response.json()) as T;
}

function bounce(here: string, canRefresh: boolean): never {
  if (canRefresh) redirect(`/api/auth/refresh?next=${encodeURIComponent(here)}`);
  redirect(`/login?next=${encodeURIComponent(here)}`);
}

async function currentPath() {
  return (await headers()).get("x-onefold-path") ?? "/home";
}

/** The builder, their enrollment and project. One API call, shared by every component in a request. */
export const getWorkspace = cache(async () => (await api<Workspace>("/workspace/"))!);

/** Whether a session cookie exists (no API call). */
export async function hasSession() {
  const jar = await cookies();
  return jar.has(ACCESS_COOKIE) || jar.has(REFRESH_COOKIE);
}

/** The signed-in workspace if there is a valid session, else null (never redirects). */
export async function optionalWorkspace(): Promise<Workspace | null> {
  const access = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!access) return null;
  const response = await fetch(`${BACKEND_URL}/api/v1/workspace/`, {
    headers: { Authorization: `Bearer ${access}` },
    cache: "no-store",
  }).catch(() => null);
  return response?.ok ? ((await response.json()) as Workspace) : null;
}

const FALLBACK_CONFIG: AuthConfig = {
  password: true,
  magic_link: true,
  providers: [],
  demo: false,
  dev_inbox_url: "",
  password_min_length: 10,
};

/** Which sign-in methods to show. Falls back to email + password if the API is down. */
export async function authConfig(): Promise<AuthConfig> {
  const response = await fetch(`${BACKEND_URL}/api/v1/auth/config/`, { cache: "no-store" }).catch(() => null);
  return response?.ok ? ((await response.json()) as AuthConfig) : FALLBACK_CONFIG;
}

/** Public GET to the API (no session), e.g. the demo accounts list. */
export async function publicApi<T>(path: string): Promise<T | null> {
  const response = await fetch(`${BACKEND_URL}/api/v1${path}`, { cache: "no-store" }).catch(() => null);
  return response?.ok ? ((await response.json()) as T) : null;
}
