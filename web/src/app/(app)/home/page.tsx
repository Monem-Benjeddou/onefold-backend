import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { ButtonLink } from "@/components/button";
import { Label } from "@/components/label";
import { Line } from "@/components/line";
import { api } from "@/lib/api";
import type { Enrollment, Page, PathOutline, Project, User } from "@/lib/types";

export const metadata: Metadata = { title: "Home" };

export default async function HomePage() {
  const [user, enrollment, path, projects] = await Promise.all([
    api<User>("/auth/me/"),
    api<Enrollment>("/learning/enrollment/"),
    api<PathOutline>("/learning/paths/current/"),
    api<Page<Project>>("/projects/"),
  ]);
  if (!enrollment) redirect("/onboarding");

  const project = projects?.results[0];
  const next = enrollment.next_step;
  const statusBySlug = new Map(enrollment.steps.map((s) => [s.slug, s.status]));
  const firstName = user?.name?.trim().split(" ")[0];

  const roles = (path?.stations ?? []).map((station) => {
    const statuses = station.steps.map((step) => statusBySlug.get(step.slug));
    const finished = statuses.every((s) => s === "done" || s === "skipped");
    const active = statuses.some((s) => s === "available" || s === "in_progress");
    return { ...station, state: finished ? "done" : active ? "now" : "ahead" };
  });

  return (
    <div className="mx-auto max-w-5xl">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Label tone="muted">{enrollment.path.title}</Label>
          <h1 className="mt-2 font-display text-4xl font-bold tracking-[-0.03em] sm:text-5xl">
            {next ? "Back at it" : "You shipped it"}
            {firstName ? `, ${firstName}.` : "."}
          </h1>
        </div>
        <p className="font-mono text-sm text-muted">
          {enrollment.totals.done} / {enrollment.totals.total} steps
        </p>
      </header>

      <div className="mt-10 grid gap-6 lg:grid-cols-[1.5fr_1fr] lg:items-start">
        <section className="border-2 border-ink bg-elevated p-6 shadow-hard-orange sm:p-8" aria-labelledby="current-build">
          <div className="flex items-center justify-between gap-4">
            <Label>Current build</Label>
            {project?.live_url && (
              <a href={project.live_url} target="_blank" rel="noreferrer" className="truncate font-mono text-xs text-muted hover:text-ink">
                {project.live_url.replace("https://", "")} ↗
              </a>
            )}
          </div>
          <h2 id="current-build" className="mt-3 font-display text-3xl font-extrabold tracking-[-0.03em]">
            {project?.name ?? "Your project"}
          </h2>
          <Line statuses={enrollment.steps.map((s) => s.status)} className="mt-5" />

          {next ? (
            <div className="mt-8">
              <p className="font-mono text-xs uppercase tracking-[0.12em] text-muted">
                Station {String(next.station_order).padStart(2, "0")} · {next.station_title} · about {next.est_minutes} min
              </p>
              <p className="mt-2 text-xl font-semibold">{next.title}</p>
              <ButtonLink href={`/steps/${next.slug}`} className="mt-6">
                {next.status === "in_progress" ? "Continue" : "Start"} →
              </ButtonLink>
            </div>
          ) : (
            <div className="mt-8">
              <p className="text-lg">Every step is done. Time to show it off.</p>
              <ButtonLink href="/ship" className="mt-6">
                See your launch →
              </ButtonLink>
            </div>
          )}
          {!project && (
            <p className="mt-6 border-l-4 border-orange bg-surface px-4 py-3 text-sm">
              Checks need a project. <Link href="/project" className="font-semibold underline underline-offset-4">Create it now</Link>.
            </p>
          )}
        </section>

        <section className="border border-line bg-surface p-6 sm:p-8" aria-labelledby="roles">
          <Label tone="muted">Roles you can cover</Label>
          <h2 id="roles" className="sr-only">Roles you can cover</h2>
          <ul className="mt-5 space-y-3">
            {roles.map((role) => (
              <li key={role.slug} className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-3">
                  <span
                    aria-hidden="true"
                    className={`h-3 w-3 ${role.state === "done" ? "bg-patina" : role.state === "now" ? "bg-orange" : "border border-line"}`}
                  />
                  <span className={role.state === "ahead" ? "text-muted" : "font-semibold"}>{role.role}</span>
                </span>
                <span className="font-mono text-xs text-muted">
                  {role.state === "done" ? "Covered" : role.state === "now" ? "Learning" : "Ahead"}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
