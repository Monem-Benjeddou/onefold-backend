import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { BACKEND_URL, REFRESH_COOKIE, clearSessionCookies } from "@/lib/session";

/** Revoke the refresh token on the API and clear the cookies. */
export async function POST() {
  const refresh = (await cookies()).get(REFRESH_COOKIE)?.value;
  if (refresh) {
    await fetch(`${BACKEND_URL}/api/v1/auth/logout/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
      cache: "no-store",
    }).catch(() => undefined);
  }
  const response = new NextResponse(null, { status: 303, headers: { Location: "/" } });
  clearSessionCookies(response);
  return response;
}
