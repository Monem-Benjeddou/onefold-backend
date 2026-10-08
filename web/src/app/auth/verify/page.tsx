import type { Metadata } from "next";

import { AuthHeading, AuthShell } from "@/components/auth/auth-shell";
import { Button, ButtonLink } from "@/components/button";

import { NextField } from "./next-field";

export const metadata: Metadata = { title: "Confirm sign-in" };

/**
 * The emailed sign-in link lands here. Signing in takes one click (a POST) so
 * that email security scanners, which open links, can't use up the token.
 */
export default async function VerifyPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token } = await searchParams;
  return (
    <AuthShell>
      {token ? (
        <form action="/api/auth/verify" method="post">
          <AuthHeading eyebrow="One click left" title="Sign in to Onefold">
            Confirm it&rsquo;s you and we&rsquo;ll take you to your build.
          </AuthHeading>
          <input type="hidden" name="token" value={token} />
          <NextField />
          <Button type="submit" className="mt-8 w-full" autoFocus>
            Sign in
          </Button>
        </form>
      ) : (
        <div>
          <AuthHeading eyebrow="Sign-in link" title="This link is missing its token">
            Open the link from your email again, or request a new one.
          </AuthHeading>
          <ButtonLink href="/login?mode=link" className="mt-8 w-full">
            Get a new link
          </ButtonLink>
        </div>
      )}
    </AuthShell>
  );
}
