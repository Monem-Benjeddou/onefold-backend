import type { Metadata } from "next";
import Link from "next/link";

import { Label } from "@/components/label";
import { Line } from "@/components/line";
import { StatusPill } from "@/components/status-pill";
import { api, getWorkspace } from "@/lib/api";
import type { PathOutline } from "@/lib/types";

export const metadata: Metadata = { title: "Path" };

const TYPE_TEXT = { learn: "Read", build: "Build", check: "Check", ship: "Ship" } as const;

export default async function PathPage() {
  const [path, workspace] = await Promise.all([api<PathOutline>("/learning/paths/current/"), getWorkspace()]);
  const enrollment = workspace.enrollment!;
  const status = new Map(enrollment.steps.map((s) => [s.slug, s.status]));

  return (
    <div className="mx-auto max-w-4xl">
      <Label tone="muted">The path</Label>
      <h1 className="mt-2 font-display text-4xl font-bold tracking-[-0.03em] sm:text-5xl">{path?.title ?? enrollment.path.title}</h1>
      <p className="mt-3 max-w-2xl text-lg text-body">{path?.outcome}</p>
      <Line statuses={enrollment.steps.map((s) => s.status)} className="mt-8" />
      <p className="mt-3 text-sm text-muted">Locked steps are open to read ahead. They unlock in order as you finish the ones before.</p>

      <ol className="mt-12 space-y-10">
        {path?.stations.map((station) => (
          <li key={station.slug}>
            <div className="flex items-baseline gap-4 border-b-2 border-ink pb-3">
              <span className="font-mono text-sm text-orange-dark">{String(station.order).padStart(2, "0")}</span>
              <h2 className="font-display text-2xl font-bold">{station.title}</h2>
              <span className="ml-auto font-mono text-xs uppercase tracking-[0.12em] text-muted">{station.role}</span>
            </div>
            <ul className="divide-y divide-line">
              {station.steps.map((step) => {
                const s = status.get(step.slug) ?? "locked";
                return (
                  <li key={step.slug}>
                    <Link
                      href={`/steps/${step.slug}`}
                      className="flex min-h-14 flex-wrap items-center gap-x-4 gap-y-1 py-3 hover:bg-surface sm:flex-nowrap"
                    >
                      <span className={`min-w-0 flex-1 ${s === "locked" ? "text-muted" : "font-semibold"}`}>{step.title}</span>
                      <span className="hidden font-mono text-xs uppercase text-muted sm:inline">
                        {TYPE_TEXT[step.type]}
                        {step.has_check ? " · checked" : ""}
                      </span>
                      <span className="w-16 font-mono text-xs text-muted sm:text-right">{step.est_minutes} min</span>
                      <StatusPill status={s} className="sm:w-28 sm:justify-center" />
                    </Link>
                  </li>
                );
              })}
            </ul>
          </li>
        ))}
      </ol>
    </div>
  );
}
