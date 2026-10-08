import { NextResponse } from "next/server";

import { authApi, readBody } from "@/lib/auth";

/** Email a password reset link (the answer never reveals whether the account exists). */
export async function POST(request: Request) {
  const { json, fields } = await readBody(request);
  const result = await authApi(request, "password/forgot/", { email: fields.email });
  if (json) return NextResponse.json(result.data, { status: result.status });
  const email = encodeURIComponent(fields.email ?? "");
  const location = result.ok ? `/forgot-password?sent=1&email=${email}` : `/forgot-password?error=${String(result.data.code ?? "error")}&email=${email}`;
  return new NextResponse(null, { status: 303, headers: { Location: location } });
}
