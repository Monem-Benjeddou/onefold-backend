"use client";

import { useEffect } from "react";

import { Button, ButtonLink } from "@/components/button";
import { Logo } from "@/components/logo";

export default function RootError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <main id="main" className="flex min-h-dvh flex-col items-start justify-center gap-6 bg-paper px-6 sm:px-16">
      <Logo />
      <h1 className="font-display text-5xl font-extrabold tracking-[-0.04em]">This page didn&rsquo;t load.</h1>
      <p className="max-w-xl text-lg text-body">It&rsquo;s on us, not you. Try again in a moment.</p>
      <div className="flex flex-wrap gap-4">
        <Button onClick={reset}>Try again</Button>
        <ButtonLink href="/" variant="secondary">
          Go home
        </ButtonLink>
      </div>
      {error.digest && <p className="font-mono text-xs text-muted">Reference: {error.digest}</p>}
    </main>
  );
}
