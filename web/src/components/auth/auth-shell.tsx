import Link from "next/link";
import type { ReactNode } from "react";

import { Logo } from "@/components/logo";

const STATIONS = ["Idea", "Product", "UX/UI", "System", "Build", "Test", "Deploy", "Run", "Iterate"];

/**
 * Split layout for every sign-in screen: the brand on Carbon (desktop only),
 * the form on Paper. On phones it is one column with a slim header.
 */
export function AuthShell({
  children,
  aside,
  headline = "Make it exist.",
  subline = "Learn every role a product team splits by shipping a real product, from idea to a live URL.",
}: {
  children: ReactNode;
  /** Top-right of the form column, e.g. "New here? Create an account". */
  aside?: ReactNode;
  headline?: string;
  subline?: string;
}) {
  return (
    <div className="min-h-dvh bg-paper lg:grid lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <aside className="relative hidden overflow-hidden bg-carbon px-12 py-10 text-paper lg:flex lg:min-h-dvh lg:flex-col lg:justify-between">
        <Link href="/" aria-label="Onefold home" className="relative self-start">
          <Logo tone="paper" />
        </Link>
        <div className="relative max-w-md">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-orange">Idea → production</p>
          <p className="mt-5 font-display text-5xl font-extrabold leading-[0.95] tracking-[-0.04em] xl:text-6xl">{headline}</p>
          <p className="mt-6 text-lg leading-relaxed text-carbon-muted">{subline}</p>
        </div>
        <ol className="relative grid grid-cols-3 gap-x-3 gap-y-4" aria-label="The nine stations">
          {STATIONS.map((station, index) => (
            <li key={station}>
              <span className={`block h-1.5 ${index < 6 ? "bg-patina" : index === 6 ? "bg-orange" : "bg-carbon-line"}`} />
              <span className="mt-2 block font-mono text-[0.68rem] uppercase tracking-[0.08em] text-carbon-muted">
                {String(index + 1).padStart(2, "0")} {station}
              </span>
            </li>
          ))}
        </ol>
      </aside>

      <div className="flex min-h-dvh flex-col">
        <header className="flex items-center justify-between gap-4 px-4 py-5 sm:px-8">
          <Link href="/" aria-label="Onefold home" className="lg:invisible">
            <Logo size={24} />
          </Link>
          <div className="text-sm text-body">{aside}</div>
        </header>
        <main id="main" className="flex flex-1 justify-center px-4 pb-16 pt-4 sm:items-center sm:px-8 sm:pt-0">
          <div className="w-full max-w-[27rem]">{children}</div>
        </main>
        <footer className="px-4 pb-6 text-xs text-muted sm:px-8">© {new Date().getFullYear()} Onefold</footer>
      </div>
    </div>
  );
}

export function AuthHeading({ eyebrow, title, children }: { eyebrow?: string; title: string; children?: ReactNode }) {
  return (
    <div>
      {eyebrow && <p className="font-mono text-xs font-medium uppercase tracking-[0.14em] text-orange-dark">{eyebrow}</p>}
      <h1 className="mt-2 font-display text-[2rem] font-bold leading-tight tracking-[-0.03em] sm:text-[2.25rem]">{title}</h1>
      {children && <p className="mt-2 leading-relaxed text-body">{children}</p>}
    </div>
  );
}
