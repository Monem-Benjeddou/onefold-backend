import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ACCESS_COOKIE, BACKEND_URL, REFRESH_COOKIE } from "./session";

/**
 * Fetch from the API inside a Server Component, as the signed-in builder.
 *
 * Server Components can't write cookies, so an expired access token sends the
 * builder through /api/auth/refresh, which renews the cookies and comes back
 * to `here` (the page's own path).
 */
export async function api<T>(path: string, here = "/home"): Promise<T | null> {
  const jar = await cookies();
  const access = jar.get(ACCESS_COOKIE)?.value;
  if (!access) bounce(here, jar.has(REFRESH_COOKIE));

  const response = await fetch(`${BACKEND_URL}/api/v1${path}`, {
    headers: { Authorization: `Bearer ${access}` },
    cache: "no-store",
  });
  if (response.status === 401) bounce(here, jar.has(REFRESH_COOKIE));
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`API ${path} failed with ${response.status}`);
  return (await response.json()) as T;
}

function bounce(here: string, canRefresh: boolean): never {
  if (canRefresh) redirect(`/api/auth/refresh?next=${encodeURIComponent(here)}`);
  redirect(`/login?next=${encodeURIComponent(here)}`);
}

/** Whether a session cookie exists (no API call). */
export async function hasSession() {
  const jar = await cookies();
  return jar.has(ACCESS_COOKIE) || jar.has(REFRESH_COOKIE);
}
