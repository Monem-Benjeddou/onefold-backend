import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { clientHeaders } from "@/lib/auth";
import { BACKEND_URL, REFRESH_COOKIE, clearSessionCookies } from "@/lib/session";

/** End this device's session on the API and clear the cookies. */
export async function POST(request: Request) {
  const jar = await cookies();
  const refresh = jar.get(REFRESH_COOKIE)?.value;
  if (refresh) {
    await fetch(`${BACKEND_URL}/api/v1/auth/logout/`, {
      method: "POST",
      headers: clientHeaders(request),
      body: JSON.stringify({ refresh }),
      cache: "no-store",
    }).catch(() => undefined);
  }
  const response = new NextResponse(null, { status: 303, headers: { Location: "/login?signed_out=1" } });
  clearSessionCookies(response);
  return response;
}
