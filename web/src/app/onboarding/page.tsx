import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { Logo } from "@/components/logo";
import { api, getWorkspace } from "@/lib/api";
import type { OnboardingState } from "@/lib/types";

import { Wizard } from "./wizard";

export const metadata: Metadata = { title: "Set up your build" };

export default async function OnboardingPage({ searchParams }: { searchParams: Promise<{ step?: string }> }) {
  const [workspace, state] = await Promise.all([getWorkspace(), api<OnboardingState>("/onboarding/", "/onboarding")]);
  if (!state || state.complete) redirect("/home");
  const { step } = await searchParams;

  return (
    <div className="min-h-dvh bg-paper">
      <header className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-5 sm:px-6">
        <Link href="/" aria-label="Onefold home">
          <Logo size={24} />
        </Link>
        <div className="flex min-w-0 items-center gap-4 text-sm">
          <span className="hidden truncate text-muted sm:inline" title={workspace.user.email}>
            {workspace.user.email}
          </span>
          <form action="/api/auth/logout" method="post">
            <button type="submit" className="min-h-11 font-semibold underline-offset-4 hover:underline">
              Sign out
            </button>
          </form>
        </div>
      </header>
      <main id="main">
        <Wizard state={state} userId={workspace.user.id} firstName={workspace.user.name.split(" ")[0] ?? ""} requestedStep={Number(step) || 0} />
      </main>
    </div>
  );
}
