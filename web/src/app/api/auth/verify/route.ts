import { NextResponse } from "next/server";

import { safeNext } from "@/lib/safe-next";
import { BACKEND_URL, setSessionCookies } from "@/lib/session";

/**
 * Redeem a sign-in link. Called by the form on /auth/verify (a POST, so email
 * scanners that open links can't burn the single-use token).
 */
export async function POST(request: Request) {
  const form = await request.formData();
  const token = String(form.get("token") ?? "");
  const next = safeNext(String(form.get("next") ?? ""), "");

  const response = await fetch(`${BACKEND_URL}/api/v1/auth/magic-link/verify/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
    cache: "no-store",
  });
  if (!response.ok) {
    const data = (await response.json().catch(() => ({}))) as { code?: string };
    const error = encodeURIComponent(data.code ?? "invalid");
    return new NextResponse(null, { status: 303, headers: { Location: `/login?error=${error}` } });
  }

  const tokens = (await response.json()) as { access: string; refresh: string };
  // New builders (no enrollment yet) go through onboarding first.
  const enrollment = await fetch(`${BACKEND_URL}/api/v1/learning/enrollment/`, {
    headers: { Authorization: `Bearer ${tokens.access}` },
    cache: "no-store",
  });
  const destination = enrollment.status === 404 ? "/onboarding" : next || "/home";

  const redirect = new NextResponse(null, { status: 303, headers: { Location: destination } });
  setSessionCookies(redirect, tokens);
  return redirect;
}
