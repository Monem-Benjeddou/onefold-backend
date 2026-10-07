import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { Label } from "@/components/label";
import { Line } from "@/components/line";
import { api } from "@/lib/api";
import type { Enrollment, PathOutline, StepStatus } from "@/lib/types";

export const metadata: Metadata = { title: "Path" };

const STATUS_TEXT: Record<StepStatus, string> = {
  done: "Done",
  skipped: "Skipped",
  in_progress: "Now",
  available: "Next",
  locked: "Locked",
};

export default async function PathPage() {
  const [path, enrollment] = await Promise.all([
    api<PathOutline>("/learning/paths/current/", "/path"),
    api<Enrollment>("/learning/enrollment/", "/path"),
  ]);
  if (!enrollment || !path) redirect("/onboarding");
  const status = new Map(enrollment.steps.map((s) => [s.slug, s.status]));

  return (
    <div className="mx-auto max-w-4xl">
      <Label tone="muted">The path</Label>
      <h1 className="mt-2 font-display text-4xl font-bold tracking-[-0.03em] sm:text-5xl">{path.title}</h1>
      <p className="mt-3 max-w-2xl text-lg text-body">{path.outcome}</p>
      <Line statuses={enrollment.steps.map((s) => s.status)} className="mt-8" />

      <ol className="mt-12 space-y-10">
        {path.stations.map((station) => (
          <li key={station.slug}>
            <div className="flex items-baseline gap-4 border-b-2 border-ink pb-3">
              <span className="font-mono text-sm text-orange-dark">{String(station.order).padStart(2, "0")}</span>
              <h2 className="font-display text-2xl font-bold">{station.title}</h2>
              <span className="ml-auto font-mono text-xs uppercase tracking-[0.12em] text-muted">{station.role}</span>
            </div>
            <ul className="divide-y divide-line">
              {station.steps.map((step) => {
                const s = status.get(step.slug) ?? "locked";
                const locked = s === "locked";
                const row = (
                  <>
                    <span
                      aria-hidden="true"
                      className={`h-3 w-3 shrink-0 ${
                        s === "done" || s === "skipped" ? "bg-patina" : s === "locked" ? "border border-line" : "bg-orange"
                      }`}
                    />
                    <span className={`flex-1 ${locked ? "text-muted" : "font-semibold"}`}>{step.title}</span>
                    <span className="hidden font-mono text-xs uppercase text-muted sm:inline">
                      {step.type}
                      {step.has_check ? " · checked" : ""}
                    </span>
                    <span className="w-16 text-right font-mono text-xs text-muted">{step.est_minutes} min</span>
                    <span className={`w-14 text-right font-mono text-xs ${locked ? "text-muted" : "text-ink"}`}>{STATUS_TEXT[s]}</span>
                  </>
                );
                return (
                  <li key={step.slug}>
                    {locked ? (
                      <div className="flex items-center gap-4 py-4" aria-disabled="true">
                        {row}
                      </div>
                    ) : (
                      <Link href={`/steps/${step.slug}`} className="flex items-center gap-4 py-4 hover:bg-surface">
                        {row}
                      </Link>
                    )}
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
