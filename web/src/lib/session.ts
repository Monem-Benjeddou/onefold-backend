import "server-only";

import type { NextResponse } from "next/server";

export const BACKEND_URL = (process.env.BACKEND_URL ?? "http://localhost:8000").replace(/\/$/, "");

export const ACCESS_COOKIE = "of_access";
export const REFRESH_COOKIE = "of_refresh";

const secure = process.env.NODE_ENV === "production";

/** Tokens live in httpOnly cookies: page scripts can never read them. */
export function setSessionCookies(response: NextResponse, tokens: { access: string; refresh?: string }) {
  response.cookies.set(ACCESS_COOKIE, tokens.access, {
    httpOnly: true,
    secure,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60,
  });
  if (tokens.refresh) {
    response.cookies.set(REFRESH_COOKIE, tokens.refresh, {
      httpOnly: true,
      secure,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });
  }
}

export function clearSessionCookies(response: NextResponse) {
  response.cookies.delete(ACCESS_COOKIE);
  response.cookies.delete(REFRESH_COOKIE);
}

/** Exchange a refresh token for new tokens. Returns null when the session is over. */
export async function refreshTokens(refresh: string) {
  const response = await fetch(`${BACKEND_URL}/api/v1/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
    cache: "no-store",
  });
  if (!response.ok) return null;
  return (await response.json()) as { access: string; refresh?: string };
}
