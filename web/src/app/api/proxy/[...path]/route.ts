import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import {
  ACCESS_COOKIE,
  BACKEND_URL,
  REFRESH_COOKIE,
  clearSessionCookies,
  refreshTokens,
  setSessionCookies,
} from "@/lib/session";

type Context = { params: Promise<{ path: string[] }> };

const FORWARDED_HEADERS = ["content-type", "idempotency-key"];

/**
 * Same-origin proxy to the API for browser calls. Adds the bearer token from
 * the httpOnly cookie and renews it once if it has expired.
 */
async function handle(request: Request, { params }: Context) {
  const { path } = await params;
  const search = new URL(request.url).search;
  const target = `${BACKEND_URL}/api/v1/${path.map(encodeURIComponent).join("/")}/${search}`;
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.text();

  const jar = await cookies();
  const send = (access?: string) => {
    const headers: Record<string, string> = {};
    for (const name of FORWARDED_HEADERS) {
      const value = request.headers.get(name);
      if (value) headers[name] = value;
    }
    if (access) headers.Authorization = `Bearer ${access}`;
    return fetch(target, { method: request.method, headers, body, cache: "no-store" });
  };

  let upstream = await send(jar.get(ACCESS_COOKIE)?.value);
  let renewed: { access: string; refresh?: string } | null = null;

  if (upstream.status === 401) {
    const refresh = jar.get(REFRESH_COOKIE)?.value;
    renewed = refresh ? await refreshTokens(refresh) : null;
    if (renewed) upstream = await send(renewed.access);
  }

  const response = new NextResponse(upstream.status === 204 ? null : await upstream.text(), {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
  });
  if (renewed) setSessionCookies(response, renewed);
  else if (upstream.status === 401) clearSessionCookies(response);
  return response;
}

export { handle as DELETE, handle as GET, handle as PATCH, handle as POST };
