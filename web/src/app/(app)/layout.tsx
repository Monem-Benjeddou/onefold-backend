import Link from "next/link";
import { redirect } from "next/navigation";

import { Logo, Symbol } from "@/components/logo";
import { ToastProvider } from "@/components/toast";
import { getWorkspace } from "@/lib/api";

import { AccountMenu } from "./account-menu";
import { BottomNav, SideNav } from "./nav-links";
import { VerifyBanner } from "./verify-banner";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const workspace = await getWorkspace();
  // Enrolled and with a project, or back to onboarding (never stranded halfway).
  if (!workspace.onboarding_complete) redirect("/onboarding");
  const { user } = workspace;

  return (
    <ToastProvider>
      <div className="min-h-dvh bg-paper lg:grid lg:grid-cols-[248px_1fr] lg:bg-[linear-gradient(to_right,var(--color-carbon)_248px,var(--color-paper)_248px)]">
        {/* Desktop sidebar */}
        <aside className="sticky top-0 hidden h-dvh flex-col gap-10 bg-carbon px-5 py-7 text-paper lg:flex">
          <Link href="/home" aria-label="Onefold dashboard" className="px-2">
            <Logo tone="paper" size={24} />
          </Link>
          <SideNav />
          <div className="mt-auto">
            <AccountMenu email={user.email} name={user.name} />
          </div>
        </aside>

        {/* Phone & tablet top bar */}
        <header className="sticky top-0 z-30 flex items-center justify-between border-b-2 border-ink bg-carbon px-4 py-3 text-paper lg:hidden">
          <Link href="/home" aria-label="Onefold dashboard" className="flex min-h-11 items-center">
            <Symbol size={26} tone="paper" />
          </Link>
          <AccountMenu email={user.email} name={user.name} compact />
        </header>

        <div className="min-w-0">
          {!user.email_verified && <VerifyBanner email={user.email} />}
          <main id="main" className="px-4 pb-32 pt-8 sm:px-8 lg:px-12 lg:pb-16 lg:pt-12">
            {children}
          </main>
        </div>
        <BottomNav />
      </div>
    </ToastProvider>
  );
}
