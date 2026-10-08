"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Alert } from "@/components/alert";
import { AuthHeading } from "@/components/auth/auth-shell";
import { Divider, ProviderButtons } from "@/components/auth/providers";
import { Button } from "@/components/button";
import { Checkbox, Field, Input, PasswordInput } from "@/components/field";
import { MailIcon } from "@/components/icons";
import { errorMessage } from "@/lib/client";
import type { AuthConfig } from "@/lib/types";

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Errors = { email?: string; password?: string; form?: string; hint?: boolean };

export function LoginForm({
  config,
  next,
  initialEmail,
  initialError,
  initialMode,
  notice,
}: {
  config: AuthConfig;
  next: string;
  initialEmail: string;
  initialError: string | null;
  initialMode: "password" | "link";
  notice: string | null;
}) {
  const [mode, setMode] = useState(initialMode);
  const [email, setEmail] = useState(initialEmail);
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [errors, setErrors] = useState<Errors>(initialError ? { form: initialError } : {});
  const [busy, setBusy] = useState(false);
  const [sentTo, setSentTo] = useState<string | null>(null);
  const summary = useRef<HTMLDivElement>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (errors.form) summary.current?.focus();
  }, [errors.form]);

  function validate(): Errors {
    const found: Errors = {};
    if (!email.trim()) found.email = "Enter your email address.";
    else if (!EMAIL.test(email.trim())) found.email = "Enter an email like you@example.com.";
    if (mode === "password" && !password) found.password = "Enter your password.";
    return found;
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const found = validate();
    setErrors(found);
    if (found.email) return emailRef.current?.focus();
    if (found.password) return passwordRef.current?.focus();

    setBusy(true);
    const url = mode === "password" ? "/api/auth/login" : "/api/auth/request";
    const body = mode === "password" ? { email: email.trim(), password, remember: remember ? "1" : "0", next } : { email: email.trim() };
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).catch(() => null);
    const data = response ? await response.json().catch(() => null) : null;

    if (!response || !response.ok) {
      setBusy(false);
      const code = (data as { code?: string } | null)?.code;
      setErrors({
        form: response ? errorMessage(data) : "Can't reach Onefold. Check your connection and try again.",
        hint: code === "invalid_credentials",
      });
      if (code === "invalid_credentials") setPassword("");
      return;
    }
    if (mode === "password") {
      // A full navigation, so the next page renders with the new session.
      window.location.assign((data as { destination: string }).destination);
      return;
    }
    if (next) sessionStorage.setItem("onefold-next", next);
    setBusy(false);
    setSentTo(email.trim());
  }

  if (sentTo) {
    return (
      <div>
        <AuthHeading eyebrow="Link sent" title="Check your inbox.">
          If <strong className="text-ink">{sentTo}</strong> can sign in, a link is on its way. It works once and expires in 15
          minutes.
        </AuthHeading>
        {config.dev_inbox_url && (
          <a
            href={config.dev_inbox_url}
            target="_blank"
            rel="noreferrer"
            className="mt-8 flex min-h-11 w-full items-center justify-center gap-2 border-2 border-ink bg-ink px-5 py-3 font-semibold text-paper hover:bg-carbon-3"
          >
            <MailIcon /> Open local inbox
          </a>
        )}
        <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm">
          <button type="button" className="font-semibold underline underline-offset-4" onClick={() => setSentTo(null)}>
            Use a different email
          </button>
          <button
            type="button"
            className="font-semibold underline underline-offset-4"
            onClick={() => {
              setSentTo(null);
              setMode("password");
            }}
          >
            Sign in with a password
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <AuthHeading eyebrow="Welcome back" title="Sign in to Onefold">
        {mode === "password" ? "Pick up your build where you left it." : "We'll email you a link that signs you in. No password needed."}
      </AuthHeading>

      {notice && !errors.form && (
        <Alert tone="info" className="mt-6">
          {notice}
        </Alert>
      )}
      {errors.form && (
        <div ref={summary} tabIndex={-1} className="mt-6 outline-none">
          <Alert tone="error" title={errors.form}>
            {errors.hint && (
              <>
                Signed up with an email link or GitHub? Use that again, or{" "}
                <Link href={`/forgot-password?email=${encodeURIComponent(email)}`} className="font-semibold underline underline-offset-4">
                  set a password
                </Link>
                .
              </>
            )}
          </Alert>
        </div>
      )}

      {config.providers.length > 0 && (
        <>
          <div className="mt-8">
            <ProviderButtons providers={config.providers} next={next} />
          </div>
          <Divider>or with email</Divider>
        </>
      )}

      <form
        action={mode === "password" ? "/api/auth/login" : undefined}
        method="post"
        onSubmit={submit}
        noValidate
        className={`space-y-5 ${config.providers.length ? "" : "mt-8"}`}
      >
        <input type="hidden" name="next" value={next} />
        <Field label="Email" error={errors.email}>
          {(a11y) => (
            <Input
              {...a11y}
              ref={emailRef}
              name="email"
              type="email"
              inputMode="email"
              autoComplete="username"
              autoFocus={!initialEmail}
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
          )}
        </Field>

        {mode === "password" && (
          <>
            <Field
              label="Password"
              error={errors.password}
              aside={
                <Link
                  href={`/forgot-password${email ? `?email=${encodeURIComponent(email)}` : ""}`}
                  className="text-sm font-semibold text-orange-dark underline-offset-4 hover:underline"
                >
                  Forgot password?
                </Link>
              }
            >
              {(a11y) => (
                <PasswordInput
                  {...a11y}
                  ref={passwordRef}
                  name="password"
                  autoComplete="current-password"
                  autoFocus={Boolean(initialEmail)}
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              )}
            </Field>
            <Checkbox
              name="remember"
              value="1"
              checked={remember}
              onChange={(event) => setRemember(event.target.checked)}
              label="Keep me signed in on this device"
            />
          </>
        )}

        <Button type="submit" className="w-full" loading={busy} loadingText={mode === "password" ? "Signing in…" : "Sending…"}>
          {mode === "password" ? "Sign in" : "Email me a sign-in link"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm">
        <button
          type="button"
          className="inline-flex min-h-11 items-center gap-2 font-semibold text-ink underline-offset-4 hover:underline"
          onClick={() => {
            setErrors({});
            setMode(mode === "password" ? "link" : "password");
          }}
        >
          {mode === "password" ? (
            <>
              <MailIcon size={16} /> Email me a sign-in link instead
            </>
          ) : (
            "Sign in with a password instead"
          )}
        </button>
      </p>
    </div>
  );
}
