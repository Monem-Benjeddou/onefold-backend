import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { safeNext } from "@/lib/safe-next";
import { PERSIST_COOKIE, REFRESH_COOKIE, clearSessionCookies, refreshTokens, setSessionCookies } from "@/lib/session";

async function renew() {
  const jar = await cookies();
  const refresh = jar.get(REFRESH_COOKIE)?.value;
  const persist = jar.get(PERSIST_COOKIE)?.value !== "0";
  if (!refresh) return { tokens: null, persist, unreachable: false };
  try {
    return { tokens: await refreshTokens(refresh), persist, unreachable: false };
  } catch {
    return { tokens: null, persist, unreachable: true };
  }
}

/** Page navigations: renew the cookies, then return to where the builder was. */
export async function GET(request: Request) {
  const next = safeNext(new URL(request.url).searchParams.get("next"));
  const { tokens, persist, unreachable } = await renew();
  if (!tokens) {
    const location = unreachable ? next : `/login?next=${encodeURIComponent(next)}&expired=1`;
    const response = new NextResponse(null, { status: 302, headers: { Location: location } });
    if (!unreachable) clearSessionCookies(response);
    return response;
  }
  const response = new NextResponse(null, { status: 302, headers: { Location: next } });
  setSessionCookies(response, tokens, persist);
  return response;
}

/** Browser calls: renew silently. 401 means the session is over. */
export async function POST() {
  const { tokens, persist, unreachable } = await renew();
  if (unreachable) return NextResponse.json({ detail: "Onefold's API isn't reachable." }, { status: 503 });
  if (!tokens) {
    const response = NextResponse.json({ detail: "Your session ended. Sign in again." }, { status: 401 });
    clearSessionCookies(response);
    return response;
  }
  const response = new NextResponse(null, { status: 204 });
  setSessionCookies(response, tokens, persist);
  return response;
}
