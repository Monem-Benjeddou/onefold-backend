import type { ReactNode } from "react";

type Tone = "orange" | "muted" | "patina" | "on-dark";

const COLORS: Record<Tone, string> = {
  orange: "text-orange-dark",
  muted: "text-muted",
  patina: "text-patina",
  // Orange-dark fails contrast on Carbon; full Orange passes.
  "on-dark": "text-orange",
};

/** Mono uppercase label: the brand's system voice. */
export function Label({ children, className = "", tone = "orange" }: { children: ReactNode; className?: string; tone?: Tone }) {
  return (
    <p className={`font-mono text-xs font-medium uppercase tracking-[0.14em] ${COLORS[tone]} ${className}`}>{children}</p>
  );
}
