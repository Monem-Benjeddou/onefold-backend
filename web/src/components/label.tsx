import type { ReactNode } from "react";

/** Mono uppercase label: the brand's system voice. */
export function Label({ children, className = "", tone = "orange" }: { children: ReactNode; className?: string; tone?: "orange" | "muted" | "patina" }) {
  const color = tone === "orange" ? "text-orange-dark" : tone === "patina" ? "text-patina" : "text-muted";
  return (
    <p className={`font-mono text-xs font-medium uppercase tracking-[0.14em] ${color} ${className}`}>
      {children}
    </p>
  );
}
