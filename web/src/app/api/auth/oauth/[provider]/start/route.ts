import { NextResponse } from "next/server";

import { authApi } from "@/lib/auth";
import { safeNext } from "@/lib/safe-next";

const STATE_COOKIE = "of_oauth_state";

type Context = { params: Promise<{ provider: string }> };

/** Start "Continue with GitHub/Google": remember the state, then go to the provider. */
export async function GET(request: Request, { params }: Context) {
  const { provider } = await params;
  const next = safeNext(new URL(request.url).searchParams.get("next"), "");
  const result = await authApi(request, `oauth/${encodeURIComponent(provider)}/start/`, { next });
  if (!result.ok) {
    const code = encodeURIComponent(String(result.data.code ?? "provider_error"));
    return new NextResponse(null, { status: 303, headers: { Location: `/login?error=${code}` } });
  }
  const response = new NextResponse(null, { status: 303, headers: { Location: String(result.data.authorize_url) } });
  // Binds the provider's answer to this browser (CSRF protection for the callback).
  response.cookies.set(STATE_COOKIE, String(result.data.state), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/api/auth/oauth",
    maxAge: 10 * 60,
  });
  return response;
}
