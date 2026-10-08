import { authApi, destinationFor, readBody, respond } from "@/lib/auth";
import type { SignIn } from "@/lib/types";

/** Email + password sign-in. */
export async function POST(request: Request) {
  const { json, fields } = await readBody(request);
  const result = await authApi(request, "login/", { email: fields.email, password: fields.password });
  const errorPage = `/login?email=${encodeURIComponent(fields.email ?? "")}${fields.next ? `&next=${encodeURIComponent(fields.next)}` : ""}`;
  if (!result.ok) return respond(json, result, { errorPage });

  const signIn = result.data as unknown as SignIn;
  return respond(json, result, {
    success: { signIn, destination: destinationFor(signIn, fields.next), persist: fields.remember !== "0" && fields.remember !== "false" },
  });
}
