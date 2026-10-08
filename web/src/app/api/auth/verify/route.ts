import { authApi, destinationFor, readBody, respond } from "@/lib/auth";
import type { SignIn } from "@/lib/types";

/**
 * Redeem a sign-in link. Called by the form on /auth/verify (a POST, so email
 * scanners that open links can't burn the single-use token).
 */
export async function POST(request: Request) {
  const { fields } = await readBody(request);
  const result = await authApi(request, "magic-link/verify/", { token: fields.token });
  if (!result.ok) return respond(false, result, { errorPage: "/login?mode=link" });
  const signIn = result.data as unknown as SignIn;
  return respond(false, result, { success: { signIn, destination: destinationFor(signIn, fields.next), persist: true } });
}
