"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { BoxIcon, HomeIcon, PathIcon } from "@/components/icons";

const LINKS = [
  { href: "/home", label: "Home", Icon: HomeIcon },
  { href: "/path", label: "Path", Icon: PathIcon },
  { href: "/project", label: "Project", Icon: BoxIcon },
];

function isActive(pathname: string, href: string) {
  return pathname === href || (href === "/path" && pathname.startsWith("/steps/"));
}

export function SideNav() {
  const pathname = usePathname();
  return (
    <nav aria-label="Main" className="flex flex-col gap-1">
      {LINKS.map(({ href, label, Icon }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`flex min-h-11 items-center gap-3 border-l-4 px-3 text-sm font-semibold ${
              active ? "border-orange bg-carbon-3 text-paper" : "border-transparent text-carbon-muted hover:bg-carbon-2 hover:text-paper"
            }`}
          >
            <Icon size={18} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

/** Phones and tablets: thumb-reachable tabs. */
export function BottomNav() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-3 border-t-2 border-ink bg-carbon pb-[env(safe-area-inset-bottom)] text-paper lg:hidden"
    >
      {LINKS.map(({ href, label, Icon }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`flex h-16 flex-col items-center justify-center gap-1 text-xs font-semibold ${
              active ? "text-paper" : "text-carbon-muted"
            }`}
          >
            <span className={`flex h-7 w-12 items-center justify-center ${active ? "bg-orange text-ink" : ""}`}>
              <Icon size={18} />
            </span>
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
