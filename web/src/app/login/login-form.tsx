"use client";

import { useState } from "react";

import { Button } from "@/components/button";
import { Label } from "@/components/label";
import { errorMessage } from "@/lib/client";

export function LoginForm({
  next,
  initialError,
  showDevHint,
}: {
  next: string;
  initialError: string | null;
  showDevHint: boolean;
}) {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(initialError);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setState("sending");
    setError(null);
    const response = await fetch("/api/auth/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    }).catch(() => null);
    if (!response || !response.ok) {
      const data = response ? await response.json().catch(() => null) : null;
      setError(response ? errorMessage(data) : "Can't reach Onefold. Check your connection and retry.");
      setState("idle");
      return;
    }
    // Remember where to land after the link (the link itself opens in a new tab).
    if (next) sessionStorage.setItem("onefold-next", next);
    setState("sent");
  }

  if (state === "sent") {
    return (
      <div className="w-full max-w-md border-2 border-ink bg-elevated p-8 shadow-hard" role="status">
        <Label tone="patina">Link sent</Label>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-[-0.02em]">Check your inbox.</h1>
        <p className="mt-3 leading-relaxed text-body">
          If <strong className="text-ink">{email}</strong> can sign in, a link is on its way. It works once
          and expires in 15 minutes.
        </p>
        {showDevHint && (
          <p className="mt-5 border-l-4 border-orange bg-surface px-4 py-3 font-mono text-xs leading-relaxed text-body">
            Running locally? The link is printed in the API logs:
            <br />
            docker compose logs api
          </p>
        )}
        <button
          type="button"
          onClick={() => setState("idle")}
          className="mt-6 text-sm font-semibold underline underline-offset-4"
        >
          Use a different email
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="w-full max-w-md border-2 border-ink bg-elevated p-8 shadow-hard" noValidate>
      <Label>Sign in · no password</Label>
      <h1 className="mt-3 font-display text-3xl font-bold tracking-[-0.02em]">Start building.</h1>
      <p className="mt-2 text-body">New or returning, it&rsquo;s the same: we email you a sign-in link.</p>

      <label htmlFor="email" className="mt-8 block text-sm font-semibold">
        Email
      </label>
      <input
        id="email"
        type="email"
        autoComplete="email"
        autoFocus
        required
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? "login-error" : undefined}
        className="mt-2 block w-full border-2 border-ink bg-paper px-4 py-3 text-base outline-none focus:border-orange"
        placeholder="you@example.com"
      />
      {error && (
        <p id="login-error" role="alert" className="mt-3 text-sm font-medium text-error">
          {error}
        </p>
      )}
      <Button type="submit" className="mt-6 w-full" disabled={state === "sending" || !email.includes("@")}>
        {state === "sending" ? "Sending…" : "Email me a link"}
      </Button>
    </form>
  );
}
