import "server-only";

import type { NextResponse } from "next/server";

export const BACKEND_URL = (process.env.BACKEND_URL ?? "http://localhost:8000").replace(/\/$/, "");

export const ACCESS_COOKIE = "of_access";
export const REFRESH_COOKIE = "of_refresh";
/** "1" when the builder ticked "Remember this device" (refresh survives a browser restart). */
export const PERSIST_COOKIE = "of_persist";

const secure = process.env.NODE_ENV === "production";
const base = { httpOnly: true, secure, sameSite: "lax" as const, path: "/" };

export type Tokens = { access: string; refresh?: string };

/** Seconds until a JWT expires (0 if unreadable). The signature is the API's job. */
export function secondsLeft(jwt: string): number {
  try {
    const payload = JSON.parse(Buffer.from(jwt.split(".")[1], "base64url").toString()) as { exp?: number };
    return Math.max(0, Math.floor((payload.exp ?? 0) - Date.now() / 1000));
  } catch {
    return 0;
  }
}

type CookieWriter = Pick<NextResponse["cookies"], "set" | "delete">;

/**
 * Tokens live in httpOnly cookies, so page scripts can never read them. Each
 * cookie lives exactly as long as its token. Without "remember this device",
 * the refresh cookie is a session cookie and ends when the browser closes.
 */
export function setSessionCookies(target: { cookies: CookieWriter }, tokens: Tokens, persist = true) {
  target.cookies.set(ACCESS_COOKIE, tokens.access, { ...base, maxAge: secondsLeft(tokens.access) });
  if (tokens.refresh) {
    const maxAge = persist ? secondsLeft(tokens.refresh) : undefined;
    target.cookies.set(REFRESH_COOKIE, tokens.refresh, { ...base, maxAge });
    target.cookies.set(PERSIST_COOKIE, persist ? "1" : "0", { ...base, maxAge });
  }
}

export function clearSessionCookies(target: { cookies: CookieWriter }) {
  target.cookies.delete(ACCESS_COOKIE);
  target.cookies.delete(REFRESH_COOKIE);
  target.cookies.delete(PERSIST_COOKIE);
}

/**
 * Exchange a refresh token for new tokens. Returns null when the session is
 * over (revoked or expired); throws when the API can't be reached, so a
 * network blip never signs anyone out.
 */
export async function refreshTokens(refresh: string): Promise<Tokens | null> {
  const response = await fetch(`${BACKEND_URL}/api/v1/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
    cache: "no-store",
  });
  if (response.status === 400 || response.status === 401) return null;
  if (!response.ok) throw new Error(`Token refresh failed with ${response.status}`);
  return (await response.json()) as Tokens;
}
