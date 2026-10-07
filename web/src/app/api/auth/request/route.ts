import { NextResponse } from "next/server";

import { BACKEND_URL } from "@/lib/session";

/** Ask the API to email a sign-in link. */
export async function POST(request: Request) {
  const { email } = (await request.json().catch(() => ({}))) as { email?: string };
  const response = await fetch(`${BACKEND_URL}/api/v1/auth/magic-link/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
    cache: "no-store",
  });
  const data = await response.json().catch(() => null);
  return NextResponse.json(data, { status: response.status });
}
