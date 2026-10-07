import type { Metadata } from "next";

import { ButtonLink, buttonClass } from "@/components/button";
import { Label } from "@/components/label";
import { Logo } from "@/components/logo";

import { NextField } from "./next-field";

export const metadata: Metadata = { title: "Confirm sign-in" };

/**
 * The emailed link lands here. Signing in takes one click (a POST) so that
 * email security scanners, which open links, can't use up the single-use token.
 */
export default async function VerifyPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token } = await searchParams;
  return (
    <main className="flex min-h-dvh items-center justify-center bg-carbon px-4 text-paper">
      <div className="w-full max-w-md">
        <Logo tone="paper" />
        {token ? (
          <form action="/api/auth/verify" method="post" className="mt-10">
            <Label className="text-orange">One click left</Label>
            <h1 className="mt-3 font-display text-4xl font-extrabold tracking-[-0.03em]">Welcome to Onefold.</h1>
            <p className="mt-3 text-carbon-muted">Confirm it&rsquo;s you and we&rsquo;ll take you to your build.</p>
            <input type="hidden" name="token" value={token} />
            <NextField />
            <button type="submit" className={buttonClass("inverse", "mt-8 w-full")} autoFocus>
              Sign in →
            </button>
          </form>
        ) : (
          <div className="mt-10">
            <h1 className="font-display text-3xl font-bold">This link is missing its token.</h1>
            <p className="mt-3 text-carbon-muted">Open the link from your email again, or request a new one.</p>
            <ButtonLink href="/login" variant="inverse" className="mt-8">
              Get a new link
            </ButtonLink>
          </div>
        )}
      </div>
    </main>
  );
}
