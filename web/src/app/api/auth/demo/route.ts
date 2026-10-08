import { authApi, destinationFor, readBody, respond } from "@/lib/auth";
import type { SignIn } from "@/lib/types";

/** Development only: one-click sign-in as a seeded demo account (the API refuses otherwise). */
export async function POST(request: Request) {
  const { json, fields } = await readBody(request);
  const result = await authApi(request, "demo/", { email: fields.email });
  if (!result.ok) return respond(json, result, {});
  const signIn = result.data as unknown as SignIn;
  return respond(json, result, { success: { signIn, destination: destinationFor(signIn, fields.next), persist: true } });
}
