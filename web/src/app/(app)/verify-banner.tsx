"use client";

import { useState } from "react";

import { MailIcon } from "@/components/icons";
import { call } from "@/lib/client";

/** Until the email is confirmed: a quiet banner with a resend button. Never blocks the app. */
export function VerifyBanner({ email }: { email: string }) {
  const [state, setState] = useState<"idle" | "sending" | "sent" | "failed">("idle");
  async function resend() {
    setState("sending");
    try {
      await call("/auth/email/resend/", { method: "POST" });
      setState("sent");
    } catch {
      setState("failed");
    }
  }
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b-2 border-ink bg-brass/30 px-4 py-2.5 text-sm sm:px-8 lg:px-12" role="status">
      <MailIcon size={16} className="shrink-0" />
      <span>
        Confirm your email: we sent a link to <strong>{email}</strong>.
      </span>
      {state === "sent" ? (
        <span className="font-semibold">✓ Sent again. Check your inbox.</span>
      ) : (
        <button type="button" onClick={resend} disabled={state === "sending"} className="min-h-9 font-semibold underline underline-offset-4">
          {state === "sending" ? "Sending…" : state === "failed" ? "Couldn't send. Try again" : "Resend link"}
        </button>
      )}
    </div>
  );
}
