"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/home", label: "Home" },
  { href: "/path", label: "Path" },
  { href: "/project", label: "Project" },
];

export function NavLinks() {
  const pathname = usePathname();
  return (
    <nav aria-label="Main" className="flex gap-1 lg:flex-col">
      {LINKS.map(({ href, label }) => {
        const active = pathname === href || (href === "/path" && pathname.startsWith("/steps/"));
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`whitespace-nowrap px-2.5 py-2 text-sm font-semibold sm:px-3 lg:border-l-4 lg:py-2.5 ${
              active
                ? "text-paper lg:border-orange lg:bg-carbon-3"
                : "text-carbon-muted hover:text-paper lg:border-transparent"
            }`}
          >
            {label}
          </Link>
        );
      })}
      <form action="/api/auth/logout" method="post" className="lg:hidden">
        <button type="submit" className="whitespace-nowrap px-2.5 py-2 text-sm font-semibold text-carbon-muted hover:text-paper">
          Sign out
        </button>
      </form>
    </nav>
  );
}
