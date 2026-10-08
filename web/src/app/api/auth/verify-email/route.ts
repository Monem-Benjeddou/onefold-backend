import { NextResponse } from "next/server";

import { authApi, readBody } from "@/lib/auth";

/**
 * Confirm an email address. The emailed link opens a page with a button that
 * posts here, so email scanners that open links can't use up the token.
 */
export async function POST(request: Request) {
  const { fields } = await readBody(request);
  const result = await authApi(request, "email/verify/", { token: fields.token });
  const location = result.ok ? "/verify-email?done=1" : `/verify-email?error=${encodeURIComponent(String(result.data.code ?? "invalid"))}`;
  return new NextResponse(null, { status: 303, headers: { Location: location } });
}
