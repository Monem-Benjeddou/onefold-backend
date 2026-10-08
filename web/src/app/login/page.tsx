import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { AuthShell } from "@/components/auth/auth-shell";
import { DemoAccounts } from "@/components/auth/demo-accounts";
import { authConfig, optionalWorkspace, publicApi } from "@/lib/api";
import { authError } from "@/lib/auth-messages";
import { safeNext } from "@/lib/safe-next";
import type { DemoAccount } from "@/lib/types";

import { LoginForm } from "./login-form";

export const metadata: Metadata = { title: "Sign in" };

type Search = { next?: string; error?: string; email?: string; mode?: string; expired?: string; signed_out?: string };

export default async function LoginPage({ searchParams }: { searchParams: Promise<Search> }) {
  const params = await searchParams;
  const next = safeNext(params.next, "");

  // Already signed in: skip the form.
  const workspace = await optionalWorkspace();
  if (workspace) redirect(workspace.onboarding_complete ? next || "/home" : "/onboarding");

  const config = await authConfig();
  const demo = config.demo ? ((await publicApi<DemoAccount[]>("/auth/demo/")) ?? []) : [];
  const notice = params.expired
    ? "Your session ended. Sign in to pick up where you left off."
    : params.signed_out
      ? "You're signed out."
      : null;

  return (
    <AuthShell
      aside={
        <>
          New here?{" "}
          <Link href={`/signup${next ? `?next=${encodeURIComponent(next)}` : ""}`} className="font-semibold text-ink underline underline-offset-4">
            Create an account
          </Link>
        </>
      }
    >
      <LoginForm
        config={config}
        next={next}
        initialEmail={params.email ?? ""}
        initialError={authError(params.error)}
        initialMode={params.mode === "link" ? "link" : "password"}
        notice={notice}
      />
      <DemoAccounts accounts={demo} next={next} />
    </AuthShell>
  );
}
