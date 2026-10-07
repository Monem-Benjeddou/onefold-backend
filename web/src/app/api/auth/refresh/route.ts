import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { safeNext } from "@/lib/safe-next";
import { REFRESH_COOKIE, clearSessionCookies, refreshTokens, setSessionCookies } from "@/lib/session";

/** Renew the session cookies, then return to where the builder was. */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const next = safeNext(url.searchParams.get("next"));
  const refresh = (await cookies()).get(REFRESH_COOKIE)?.value;
  const tokens = refresh ? await refreshTokens(refresh) : null;

  if (!tokens) {
    const response = new NextResponse(null, {
      status: 302,
      headers: { Location: `/login?next=${encodeURIComponent(next)}` },
    });
    clearSessionCookies(response);
    return response;
  }
  const response = new NextResponse(null, { status: 302, headers: { Location: next } });
  setSessionCookies(response, tokens);
  return response;
}
