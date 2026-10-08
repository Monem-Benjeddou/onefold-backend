"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Alert } from "@/components/alert";
import { AuthHeading } from "@/components/auth/auth-shell";
import { PasswordStrength, passwordRules } from "@/components/auth/password-strength";
import { Divider, ProviderButtons } from "@/components/auth/providers";
import { Button } from "@/components/button";
import { Field, Input, PasswordInput } from "@/components/field";
import { errorMessage } from "@/lib/client";
import type { AuthConfig } from "@/lib/types";

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Errors = { name?: string; email?: string; password?: string; form?: string; taken?: boolean };

export function SignupForm({
  config,
  initialEmail,
  initialError,
}: {
  config: AuthConfig;
  initialEmail: string;
  initialError: string | null;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState(initialEmail);
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors>(initialError ? { form: initialError } : {});
  const [busy, setBusy] = useState(false);
  const summary = useRef<HTMLDivElement>(null);
  const refs = {
    email: useRef<HTMLInputElement>(null),
    password: useRef<HTMLInputElement>(null),
  };

  useEffect(() => {
    if (errors.form) summary.current?.focus();
  }, [errors.form]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const found: Errors = {};
    if (!email.trim()) found.email = "Enter your email address.";
    else if (!EMAIL.test(email.trim())) found.email = "Enter an email like you@example.com.";
    const unmet = passwordRules(password, email, config.password_min_length).find((rule) => !rule.met);
    if (!password) found.password = "Choose a password.";
    else if (unmet) found.password = `Your password needs to meet this rule: ${unmet.label.toLowerCase()}.`;
    setErrors(found);
    if (found.email) return refs.email.current?.focus();
    if (found.password) return refs.password.current?.focus();

    setBusy(true);
    const response = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name.trim(), email: email.trim(), password }),
    }).catch(() => null);
    const data = (response ? await response.json().catch(() => null) : null) as Record<string, unknown> | null;
    if (response?.ok && data) {
      window.location.assign(String(data.destination));
      return;
    }
    setBusy(false);
    if (!response) return setErrors({ form: "Can't reach Onefold. Check your connection and try again." });
    const fieldErrors: Errors = {};
    if (Array.isArray(data?.email)) fieldErrors.email = String(data.email[0]);
    if (Array.isArray(data?.password)) fieldErrors.password = (data.password as string[]).join(" ");
    if (data?.code === "email_taken") fieldErrors.taken = true;
    if (!fieldErrors.email && !fieldErrors.password) fieldErrors.form = errorMessage(data);
    setErrors(fieldErrors);
    if (fieldErrors.email) refs.email.current?.focus();
    else if (fieldErrors.password) refs.password.current?.focus();
  }

  return (
    <div>
      <AuthHeading eyebrow="Create your account" title="Start building">
        Free to start. Your first step takes about 10 minutes.
      </AuthHeading>

      {errors.form && (
        <div ref={summary} tabIndex={-1} className="mt-6 outline-none">
          <Alert tone="error" title={errors.form} />
        </div>
      )}

      {config.providers.length > 0 && (
        <>
          <div className="mt-8">
            <ProviderButtons providers={config.providers} />
          </div>
          <Divider>or with email</Divider>
        </>
      )}

      <form action="/api/auth/signup" method="post" onSubmit={submit} noValidate className={`space-y-5 ${config.providers.length ? "" : "mt-8"}`}>
        <Field label="Your name" optional hint="What we call you in the app.">
          {(a11y) => (
            <Input {...a11y} name="name" autoComplete="name" value={name} maxLength={120} onChange={(e) => setName(e.target.value)} />
          )}
        </Field>
        <Field
          label="Email"
          error={errors.email}
          hint="We'll send a link to confirm it's yours."
        >
          {(a11y) => (
            <Input
              {...a11y}
              ref={refs.email}
              name="email"
              type="email"
              inputMode="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          )}
        </Field>
        {errors.taken && (
          <p className="-mt-2 text-sm">
            <Link href={`/login?email=${encodeURIComponent(email)}`} className="font-semibold underline underline-offset-4">
              Sign in instead
            </Link>{" "}
            or{" "}
            <Link href={`/forgot-password?email=${encodeURIComponent(email)}`} className="font-semibold underline underline-offset-4">
              reset your password
            </Link>
            .
          </p>
        )}
        <Field label="Password" error={errors.password}>
          {(a11y) => (
            <>
              <PasswordInput
                {...a11y}
                ref={refs.password}
                name="password"
                autoComplete="new-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <PasswordStrength password={password} email={email} min={config.password_min_length} />
            </>
          )}
        </Field>
        <Button type="submit" className="w-full" loading={busy} loadingText="Creating your account…">
          Create account
        </Button>
        <p className="text-xs leading-relaxed text-muted">
          Your projects stay unlisted until you choose to share them.
        </p>
      </form>
    </div>
  );
}
