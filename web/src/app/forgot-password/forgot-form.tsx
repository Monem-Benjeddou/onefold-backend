"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Alert } from "@/components/alert";
import { AuthHeading } from "@/components/auth/auth-shell";
import { InboxLink } from "@/components/auth/inbox-link";
import { Button } from "@/components/button";
import { Field, Input } from "@/components/field";
import { errorMessage } from "@/lib/client";

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const COOLDOWN = 60;

export function ForgotForm({
  initialEmail,
  initiallySent,
  initialError,
  inboxUrl,
}: {
  initialEmail: string;
  initiallySent: boolean;
  initialError: string | null;
  inboxUrl: string;
}) {
  const [email, setEmail] = useState(initialEmail);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(initialError);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(initiallySent);
  const [wait, setWait] = useState(initiallySent ? COOLDOWN : 0);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (wait <= 0) return;
    const timer = setTimeout(() => setWait(wait - 1), 1000);
    return () => clearTimeout(timer);
  }, [wait]);

  async function send(event?: React.FormEvent) {
    event?.preventDefault();
    if (!EMAIL.test(email.trim())) {
      setError(email.trim() ? "Enter an email like you@example.com." : "Enter your email address.");
      input.current?.focus();
      return;
    }
    setError(null);
    setFormError(null);
    setBusy(true);
    const response = await fetch("/api/auth/forgot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim() }),
    }).catch(() => null);
    setBusy(false);
    if (!response?.ok) {
      setFormError(response ? errorMessage(await response.json().catch(() => null)) : "Can't reach Onefold. Try again.");
      return;
    }
    setSent(true);
    setWait(COOLDOWN);
  }

  if (sent) {
    return (
      <div>
        <AuthHeading eyebrow="Check your inbox" title="Reset link sent">
          If an account exists for <strong className="text-ink">{email}</strong>, we sent a link to choose a new password. It
          works once and expires in 30 minutes.
        </AuthHeading>
        <InboxLink url={inboxUrl} />
        {formError && <Alert tone="error" className="mt-6" title={formError} />}
        <div className="mt-8 space-y-3 text-sm text-body">
          <p>Nothing after a few minutes? Check spam, or</p>
          <Button variant="secondary" className="w-full" onClick={() => send()} disabled={wait > 0} loading={busy} loadingText="Sending…">
            {wait > 0 ? `Send again in ${wait}s` : "Send the link again"}
          </Button>
          <button type="button" onClick={() => setSent(false)} className="min-h-11 font-semibold underline underline-offset-4">
            Use a different email
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <AuthHeading eyebrow="Account recovery" title="Forgot your password?">
        Enter your email and we&rsquo;ll send a link to choose a new one. This also works if you signed up with an email link
        or GitHub and want a password.
      </AuthHeading>
      {formError && <Alert tone="error" className="mt-6" title={formError} />}
      <form action="/api/auth/forgot" method="post" onSubmit={send} noValidate className="mt-8 space-y-5">
        <Field label="Email" error={error}>
          {(a11y) => (
            <Input
              {...a11y}
              ref={input}
              name="email"
              type="email"
              inputMode="email"
              autoComplete="email"
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          )}
        </Field>
        <Button type="submit" className="w-full" loading={busy} loadingText="Sending…">
          Send reset link
        </Button>
      </form>
      <p className="mt-6 text-center text-sm">
        Remembered it?{" "}
        <Link href={`/login${email ? `?email=${encodeURIComponent(email)}` : ""}`} className="font-semibold underline underline-offset-4">
          Sign in
        </Link>
      </p>
    </div>
  );
}
