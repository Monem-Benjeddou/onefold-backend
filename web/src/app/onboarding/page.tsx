import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { Logo } from "@/components/logo";
import { api } from "@/lib/api";
import type { Enrollment } from "@/lib/types";

import { Wizard } from "./wizard";

export const metadata: Metadata = { title: "Get started" };

export default async function OnboardingPage() {
  const enrollment = await api<Enrollment>("/learning/enrollment/", "/onboarding");
  if (enrollment) redirect("/home");
  return (
    <main className="min-h-dvh bg-paper">
      <header className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        <Logo />
      </header>
      <Wizard />
    </main>
  );
}
