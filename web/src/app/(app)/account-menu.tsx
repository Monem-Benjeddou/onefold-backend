"use client";

import { useEffect, useRef, useState } from "react";

import { LogOutIcon } from "@/components/icons";

/** The signed-in account and Sign out. A disclosure menu, closed by Escape or an outside click. */
export function AccountMenu({ email, name, compact = false }: { email: string; name: string; compact?: boolean }) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const initial = (name || email).trim()[0]?.toUpperCase() ?? "?";

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent | KeyboardEvent) => {
      if (event instanceof KeyboardEvent ? event.key === "Escape" : !root.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);

  return (
    <div ref={root} className="relative">
      <button
        type="button"
        aria-expanded={open}
        aria-controls="account-menu"
        onClick={() => setOpen(!open)}
        className={`flex min-h-11 items-center gap-3 text-left ${compact ? "" : "w-full px-2 hover:bg-carbon-2"}`}
      >
        <span className="flex h-8 w-8 shrink-0 items-center justify-center bg-orange font-display text-sm font-bold text-ink" aria-hidden="true">
          {initial}
        </span>
        {!compact && (
          <span className="min-w-0">
            <span className="block truncate text-sm font-semibold text-paper">{name || "Your account"}</span>
            <span className="block truncate text-xs text-carbon-muted">{email}</span>
          </span>
        )}
        <span className="sr-only">Account menu</span>
      </button>
      {open && (
        <div
          id="account-menu"
          className={`absolute z-40 w-64 border-2 border-ink bg-elevated p-2 text-ink shadow-hard ${
            compact ? "right-0 top-full mt-2" : "bottom-full left-0 mb-2"
          }`}
        >
          <p className="truncate px-3 py-2 text-xs text-muted">Signed in as {email}</p>
          <form action="/api/auth/logout" method="post">
            <button type="submit" className="flex min-h-11 w-full items-center gap-2 px-3 text-sm font-semibold hover:bg-surface">
              <LogOutIcon size={16} /> Sign out
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
