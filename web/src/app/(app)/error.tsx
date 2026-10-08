"use client";

import { useEffect } from "react";

import { Button, ButtonLink } from "@/components/button";
import { Label } from "@/components/label";

/** Inside the app shell: the navigation stays, the page explains and offers a retry. */
export default function AppError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <div className="mx-auto max-w-2xl py-10">
      <Label>Something broke</Label>
      <h1 className="mt-3 font-display text-4xl font-bold tracking-[-0.03em]">This page didn&rsquo;t load.</h1>
      <p className="mt-4 text-lg leading-relaxed text-body">
        Onefold couldn&rsquo;t get what this page needs. It&rsquo;s on us, not you, and your progress is safe. Try again; if it
        keeps happening, send us the reference below.
      </p>
      <div className="mt-8 flex flex-wrap gap-4">
        <Button onClick={reset}>Try again</Button>
        <ButtonLink href="/home" variant="secondary">
          Go to your dashboard
        </ButtonLink>
      </div>
      {error.digest && (
        <p className="mt-8 font-mono text-xs text-muted">
          Reference: <span className="select-all">{error.digest}</span>
        </p>
      )}
    </div>
  );
}
