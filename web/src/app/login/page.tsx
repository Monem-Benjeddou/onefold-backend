import type { Metadata } from "next";

import { Logo } from "@/components/logo";
import { safeNext } from "@/lib/safe-next";

import { LoginForm } from "./login-form";

export const metadata: Metadata = { title: "Sign in" };

const ERRORS: Record<string, string> = {
  used: "That link was already used. Get a fresh one below.",
  expired: "That link expired. Links last 15 minutes. Get a fresh one below.",
  invalid: "That link isn't valid. Get a fresh one below.",
  inactive: "This account is disabled. Contact support if that's a surprise.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; error?: string }>;
}) {
  const { next, error } = await searchParams;
  return (
    <main className="flex min-h-dvh flex-col bg-paper">
      <header className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6">
        <a href="/" aria-label="Onefold home">
          <Logo />
        </a>
      </header>
      <div className="flex flex-1 items-center justify-center px-4 pb-24">
        <LoginForm
          next={safeNext(next, "")}
          initialError={error ? (ERRORS[error] ?? ERRORS.invalid) : null}
          showDevHint={process.env.NODE_ENV !== "production"}
        />
      </div>
    </main>
  );
}
