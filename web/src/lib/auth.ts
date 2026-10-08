import "server-only";

import { NextResponse } from "next/server";

import { safeNext } from "./safe-next";
import { BACKEND_URL, setSessionCookies } from "./session";
import type { SignIn } from "./types";

/** Headers worth passing to the API for auditing and rate limits. */
export function clientHeaders(request: Request): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const agent = request.headers.get("user-agent");
  const forwarded = request.headers.get("x-forwarded-for");
  const id = request.headers.get("x-request-id");
  if (agent) headers["User-Agent"] = agent;
  if (forwarded) headers["X-Forwarded-For"] = forwarded;
  if (id) headers["X-Request-ID"] = id;
  return headers;
}

/** POST JSON to the public auth API. Never throws: an unreachable API is a 503. */
export async function authApi(request: Request, path: string, body: unknown) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/${path}`, {
      method: "POST",
      headers: clientHeaders(request),
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const data = (await response.json().catch(() => ({}))) as Record<string, unknown>;
    return { ok: response.ok, status: response.status, data };
  } catch {
    return {
      ok: false,
      status: 503,
      data: { detail: "Onefold's API isn't reachable right now. Try again in a moment.", code: "unavailable" },
    };
  }
}

/** Where a builder lands after signing in: onboarding first, then where they were going. */
export function destinationFor(signIn: SignIn, next?: string | null) {
  if (!signIn.user.onboarding_complete) return "/onboarding";
  return safeNext(next, "/home");
}

/** Read a JSON or form body (forms work without JavaScript). */
export async function readBody(request: Request): Promise<{ json: boolean; fields: Record<string, string> }> {
  const type = request.headers.get("content-type") ?? "";
  if (type.includes("application/json")) {
    const data = (await request.json().catch(() => ({}))) as Record<string, unknown>;
    return { json: true, fields: Object.fromEntries(Object.entries(data).map(([k, v]) => [k, String(v ?? "")])) };
  }
  const form = await request.formData().catch(() => null);
  const fields: Record<string, string> = {};
  form?.forEach((value, key) => {
    if (typeof value === "string") fields[key] = value;
  });
  return { json: false, fields };
}

/**
 * Answer a sign-in form: JSON for the JavaScript form, a 303 redirect for a
 * plain form post. On success, sets the session cookies.
 */
export function respond(
  json: boolean,
  result: { status: number; data: Record<string, unknown> },
  options: { success?: { signIn: SignIn; destination: string; persist: boolean }; errorPage?: string },
) {
  if (options.success) {
    const { signIn, destination, persist } = options.success;
    const response = json
      ? NextResponse.json({ destination })
      : new NextResponse(null, { status: 303, headers: { Location: destination } });
    setSessionCookies(response, signIn, persist);
    return response;
  }
  if (json) return NextResponse.json(result.data, { status: result.status });
  const code = typeof result.data.code === "string" ? result.data.code : "error";
  const page = options.errorPage ?? "/login";
  const separator = page.includes("?") ? "&" : "?";
  return new NextResponse(null, { status: 303, headers: { Location: `${page}${separator}error=${encodeURIComponent(code)}` } });
}
