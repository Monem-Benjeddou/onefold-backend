import { Logo, Symbol } from "@/components/logo";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";

import { NavLinks } from "./nav-links";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const user = await api<User>("/auth/me/");
  return (
    <div className="min-h-dvh bg-paper lg:grid lg:grid-cols-[240px_1fr] lg:bg-[linear-gradient(to_right,var(--color-carbon)_240px,var(--color-paper)_240px)]">
      <aside className="sticky top-0 z-20 flex items-center justify-between border-b-2 border-ink bg-carbon px-4 py-3 text-paper lg:h-dvh lg:flex-col lg:items-stretch lg:justify-start lg:gap-10 lg:border-b-0 lg:px-5 lg:py-7">
        <a href="/home" aria-label="Onefold dashboard">
          <Symbol size={26} tone="paper" className="lg:hidden" />
          <span className="hidden lg:block">
            <Logo tone="paper" size={24} />
          </span>
        </a>
        <NavLinks />
        <div className="hidden lg:mt-auto lg:block">
          <p className="truncate text-sm text-carbon-muted" title={user?.email}>
            {user?.email}
          </p>
          <form action="/api/auth/logout" method="post">
            <button type="submit" className="mt-2 text-sm font-semibold text-paper underline-offset-4 hover:underline">
              Sign out
            </button>
          </form>
        </div>
      </aside>
      <main className="min-w-0 px-4 py-8 sm:px-8 lg:px-12 lg:py-12">{children}</main>
    </div>
  );
}
