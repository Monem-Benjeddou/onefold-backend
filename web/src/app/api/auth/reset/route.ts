import { authApi, destinationFor, readBody, respond } from "@/lib/auth";
import type { SignIn } from "@/lib/types";

/** Set a new password from a reset link; signs the builder in on this device. */
export async function POST(request: Request) {
  const { json, fields } = await readBody(request);
  const result = await authApi(request, "password/reset/", { token: fields.token, password: fields.password });
  if (!result.ok) {
    return respond(json, result, { errorPage: `/reset-password?token=${encodeURIComponent(fields.token ?? "")}` });
  }
  const signIn = result.data as unknown as SignIn;
  return respond(json, result, { success: { signIn, destination: destinationFor(signIn), persist: true } });
}
