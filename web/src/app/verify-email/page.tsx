import type { Metadata } from "next";

import { Alert } from "@/components/alert";
import { AuthHeading, AuthShell } from "@/components/auth/auth-shell";
import { Button, ButtonLink } from "@/components/button";
import { hasSession } from "@/lib/api";
import { authError } from "@/lib/auth-messages";

export const metadata: Metadata = { title: "Confirm your email" };

/**
 * The confirmation email links here. Confirming takes one click (a POST) so
 * that email scanners, which open links, can't use up the single-use token.
 */
export default async function VerifyEmailPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string; done?: string; error?: string }>;
}) {
  const { token, done, error } = await searchParams;
  const signedIn = await hasSession();
  const onward = signedIn ? (
    <ButtonLink href="/home" className="mt-8 w-full">
      Continue to Onefold
    </ButtonLink>
  ) : (
    <ButtonLink href="/login" className="mt-8 w-full">
      Sign in
    </ButtonLink>
  );

  return (
    <AuthShell>
      {done ? (
        <div>
          <AuthHeading eyebrow="All set" title="Email confirmed" />
          <Alert tone="success" className="mt-6">
            You can always get back into your account with this address.
          </Alert>
          {onward}
        </div>
      ) : error ? (
        <div>
          <AuthHeading eyebrow="Confirm your email" title="That link didn't work" />
          <Alert tone="error" className="mt-6" title={authError(error)}>
            {signedIn
              ? "Use the banner in the app to send a new confirmation link."
              : "Sign in, then send a new link from the banner at the top of the app."}
          </Alert>
          {onward}
        </div>
      ) : token ? (
        <form action="/api/auth/verify-email" method="post">
          <AuthHeading eyebrow="One click left" title="Confirm your email">
            This proves the address is yours, so you can always get back in.
          </AuthHeading>
          <input type="hidden" name="token" value={token} />
          <Button type="submit" className="mt-8 w-full" autoFocus>
            Confirm my email
          </Button>
        </form>
      ) : (
        <div>
          <AuthHeading eyebrow="Confirm your email" title="This link is incomplete">
            Open the link from your email again.
          </AuthHeading>
          {onward}
        </div>
      )}
    </AuthShell>
  );
}
