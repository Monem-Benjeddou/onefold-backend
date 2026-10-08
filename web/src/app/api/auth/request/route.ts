import { NextResponse } from "next/server";

import { authApi, readBody } from "@/lib/auth";

/** Ask the API to email a sign-in link. */
export async function POST(request: Request) {
  const { fields } = await readBody(request);
  const result = await authApi(request, "magic-link/", { email: fields.email });
  return NextResponse.json(result.data, { status: result.status });
}
