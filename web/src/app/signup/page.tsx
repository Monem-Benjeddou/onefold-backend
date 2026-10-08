import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { AuthShell } from "@/components/auth/auth-shell";
import { authConfig, optionalWorkspace } from "@/lib/api";
import { authError } from "@/lib/auth-messages";
import { safeNext } from "@/lib/safe-next";

import { SignupForm } from "./signup-form";

export const metadata: Metadata = { title: "Create your account" };

export default async function SignupPage({ searchParams }: { searchParams: Promise<{ email?: string; error?: string; next?: string }> }) {
  const params = await searchParams;
  const workspace = await optionalWorkspace();
  if (workspace) redirect(workspace.onboarding_complete ? "/home" : "/onboarding");
  const config = await authConfig();
  const next = safeNext(params.next, "");

  return (
    <AuthShell
      headline="Start with an idea. Finish with a URL."
      subline="One path, nine stations, every role a product team splits. You build it with your own tools; we check the work."
      aside={
        <>
          Have an account?{" "}
          <Link href={`/login${next ? `?next=${encodeURIComponent(next)}` : ""}`} className="font-semibold text-ink underline underline-offset-4">
            Sign in
          </Link>
        </>
      }
    >
      <SignupForm config={config} initialEmail={params.email ?? ""} initialError={authError(params.error)} />
    </AuthShell>
  );
}
