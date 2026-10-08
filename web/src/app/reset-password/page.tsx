import type { Metadata } from "next";
import Link from "next/link";

import { Alert } from "@/components/alert";
import { AuthHeading, AuthShell } from "@/components/auth/auth-shell";
import { ButtonLink } from "@/components/button";
import { authConfig } from "@/lib/api";
import { authError } from "@/lib/auth-messages";

import { ResetForm } from "./reset-form";

export const metadata: Metadata = { title: "Choose a new password" };

export default async function ResetPage({ searchParams }: { searchParams: Promise<{ token?: string; error?: string }> }) {
  const { token, error } = await searchParams;
  const config = await authConfig();
  return (
    <AuthShell
      aside={
        <Link href="/login" className="font-semibold text-ink underline underline-offset-4">
          Back to sign in
        </Link>
      }
    >
      {token ? (
        <ResetForm token={token} min={config.password_min_length} initialError={authError(error)} />
      ) : (
        <div>
          <AuthHeading eyebrow="Reset link" title="This link is incomplete">
            Open the link from your email again, or ask for a new one.
          </AuthHeading>
          <Alert tone="warning" className="mt-6">
            Reset links only work once and expire after 30 minutes.
          </Alert>
          <ButtonLink href="/forgot-password" className="mt-8 w-full">
            Send a new link
          </ButtonLink>
        </div>
      )}
    </AuthShell>
  );
}
