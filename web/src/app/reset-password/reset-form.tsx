"use client";

import { useEffect, useRef, useState } from "react";

import { Alert } from "@/components/alert";
import { AuthHeading } from "@/components/auth/auth-shell";
import { PasswordStrength, passwordRules } from "@/components/auth/password-strength";
import { Button, ButtonLink } from "@/components/button";
import { Field, PasswordInput } from "@/components/field";
import { errorMessage } from "@/lib/client";

const LINK_PROBLEMS = new Set(["invalid", "used", "expired"]);

export function ResetForm({ token, min, initialError }: { token: string; min: number; initialError: string | null }) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<{ password?: string; confirm?: string; form?: string; link?: boolean }>(
    initialError ? { form: initialError, link: true } : {},
  );
  const [busy, setBusy] = useState(false);
  const summary = useRef<HTMLDivElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const confirmRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (errors.form) summary.current?.focus();
  }, [errors.form]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const unmet = passwordRules(password, "", min).find((rule) => !rule.met);
    if (!password || unmet) {
      setErrors({ password: password ? `Needs: ${unmet!.label.toLowerCase()}.` : "Choose a new password." });
      return passwordRef.current?.focus();
    }
    if (password !== confirm) {
      setErrors({ confirm: "The two passwords don't match." });
      return confirmRef.current?.focus();
    }
    setBusy(true);
    setErrors({});
    const response = await fetch("/api/auth/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, password }),
    }).catch(() => null);
    const data = (response ? await response.json().catch(() => null) : null) as Record<string, unknown> | null;
    if (response?.ok && data) {
      window.location.assign(String(data.destination));
      return;
    }
    setBusy(false);
    if (Array.isArray(data?.password)) {
      setErrors({ password: (data.password as string[]).join(" ") });
      return passwordRef.current?.focus();
    }
    setErrors({
      form: response ? errorMessage(data) : "Can't reach Onefold. Try again.",
      link: LINK_PROBLEMS.has(String(data?.code)),
    });
  }

  return (
    <div>
      <AuthHeading eyebrow="Account recovery" title="Choose a new password">
        You&rsquo;ll be signed in here, and signed out everywhere else.
      </AuthHeading>
      {errors.form && (
        <div ref={summary} tabIndex={-1} className="mt-6 outline-none">
          <Alert tone="error" title={errors.form} />
          {errors.link && (
            <ButtonLink href="/forgot-password" variant="secondary" className="mt-4 w-full">
              Send a new link
            </ButtonLink>
          )}
        </div>
      )}
      {!errors.link && (
        <form onSubmit={submit} noValidate className="mt-8 space-y-5">
          <Field label="New password" error={errors.password}>
            {(a11y) => (
              <>
                <PasswordInput
                  {...a11y}
                  ref={passwordRef}
                  name="password"
                  autoComplete="new-password"
                  autoFocus
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <PasswordStrength password={password} min={min} />
              </>
            )}
          </Field>
          <Field label="Type it again" error={errors.confirm}>
            {(a11y) => (
              <PasswordInput
                {...a11y}
                ref={confirmRef}
                name="confirm"
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
              />
            )}
          </Field>
          <Button type="submit" className="w-full" loading={busy} loadingText="Saving…">
            Save password and sign in
          </Button>
        </form>
      )}
    </div>
  );
}
