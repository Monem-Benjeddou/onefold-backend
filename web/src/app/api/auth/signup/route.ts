import { authApi, readBody, respond } from "@/lib/auth";
import type { SignIn } from "@/lib/types";

/** Create an account with email + password, then go to onboarding. */
export async function POST(request: Request) {
  const { json, fields } = await readBody(request);
  const result = await authApi(request, "register/", {
    name: fields.name ?? "",
    email: fields.email,
    password: fields.password,
  });
  if (!result.ok) return respond(json, result, { errorPage: `/signup?email=${encodeURIComponent(fields.email ?? "")}` });
  return respond(json, result, {
    success: { signIn: result.data as unknown as SignIn, destination: "/onboarding", persist: true },
  });
}
