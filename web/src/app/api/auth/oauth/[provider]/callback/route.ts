import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { authApi, destinationFor } from "@/lib/auth";
import { setSessionCookies } from "@/lib/session";
import type { SignIn } from "@/lib/types";

const STATE_COOKIE = "of_oauth_state";

type Context = { params: Promise<{ provider: string }> };

function back(code: string) {
  const response = new NextResponse(null, { status: 303, headers: { Location: `/login?error=${encodeURIComponent(code)}` } });
  response.cookies.delete({ name: STATE_COOKIE, path: "/api/auth/oauth" });
  return response;
}

/** The provider sends the browser back here with a code. */
export async function GET(request: Request, { params }: Context) {
  const { provider } = await params;
  const url = new URL(request.url);
  if (url.searchParams.get("error")) return back("provider_denied");

  const state = url.searchParams.get("state") ?? "";
  const expected = (await cookies()).get(STATE_COOKIE)?.value;
  if (!state || state !== expected) return back("state_invalid");

  const result = await authApi(request, `oauth/${encodeURIComponent(provider)}/callback/`, {
    code: url.searchParams.get("code") ?? "",
    state,
  });
  if (!result.ok) return back(String(result.data.code ?? "provider_error"));

  const signIn = result.data as unknown as SignIn;
  const response = new NextResponse(null, { status: 303, headers: { Location: destinationFor(signIn, signIn.next) } });
  response.cookies.delete({ name: STATE_COOKIE, path: "/api/auth/oauth" });
  setSessionCookies(response, signIn, true);
  return response;
}
