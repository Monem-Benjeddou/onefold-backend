import type { Metadata } from "next";
import Link from "next/link";

import { AuthShell } from "@/components/auth/auth-shell";
import { authConfig } from "@/lib/api";
import { authError } from "@/lib/auth-messages";

import { ForgotForm } from "./forgot-form";

export const metadata: Metadata = { title: "Reset your password" };

export default async function ForgotPage({ searchParams }: { searchParams: Promise<{ email?: string; sent?: string; error?: string }> }) {
  const params = await searchParams;
  const config = await authConfig();
  return (
    <AuthShell
      aside={
        <Link href="/login" className="font-semibold text-ink underline underline-offset-4">
          Back to sign in
        </Link>
      }
    >
      <ForgotForm
        initialEmail={params.email ?? ""}
        initiallySent={Boolean(params.sent)}
        initialError={authError(params.error)}
        inboxUrl={config.dev_inbox_url}
      />
    </AuthShell>
  );
}
