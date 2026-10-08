import { NextResponse, type NextRequest } from "next/server";

import {
  ACCESS_COOKIE,
  PERSIST_COOKIE,
  REFRESH_COOKIE,
  type Tokens,
  clearSessionCookies,
  refreshTokens,
  secondsLeft,
  setSessionCookies,
} from "@/lib/session";

/** Renew a little before expiry so a page never renders with a dying token. */
const RENEW_WITHIN_SECONDS = 60;

/**
 * Runs before every page render:
 * - renews an expired or expiring access token from the refresh cookie, and
 *   hands the fresh token to the page in the same request (no redirect hop);
 * - tells the page its own path, so a signed-out page can send the builder to
 *   /login and back.
 */
export async function proxy(request: NextRequest) {
  const headers = new Headers(request.headers);
  headers.set("x-onefold-path", request.nextUrl.pathname + request.nextUrl.search);

  const access = request.cookies.get(ACCESS_COOKIE)?.value;
  const refresh = request.cookies.get(REFRESH_COOKIE)?.value;
  let renewed: Tokens | null = null;
  let ended = false;

  if (refresh && (!access || secondsLeft(access) < RENEW_WITHIN_SECONDS)) {
    try {
      renewed = await refreshTokens(refresh);
      ended = renewed === null;
    } catch {
      // API unreachable: leave the cookies alone; the page shows its error state.
    }
  }

  if (renewed) {
    request.cookies.set(ACCESS_COOKIE, renewed.access);
    if (renewed.refresh) request.cookies.set(REFRESH_COOKIE, renewed.refresh);
    headers.set("cookie", request.cookies.toString());
  } else if (ended) {
    request.cookies.delete(ACCESS_COOKIE);
    request.cookies.delete(REFRESH_COOKIE);
    headers.set("cookie", request.cookies.toString());
  }

  const response = NextResponse.next({ request: { headers } });
  if (renewed) setSessionCookies(response, renewed, request.cookies.get(PERSIST_COOKIE)?.value !== "0");
  else if (ended) clearSessionCookies(response);
  return response;
}

export const config = {
  // Pages only: not API routes, any Next internals (/_next/*, including the
  // dev server's hot-reload socket) or files with an extension.
  matcher: ["/((?!api/|_next/|.*\\.[a-zA-Z0-9]+$).*)"],
};
