import type { Metadata } from "next";

import { Label } from "@/components/label";
import { api } from "@/lib/api";
import type { CheckRun, Page, Project } from "@/lib/types";

import { ProjectForm } from "./project-form";
import { TokenBox } from "./token-box";

export const metadata: Metadata = { title: "Project" };

const STATUS_STYLE: Record<CheckRun["status"], string> = {
  passed: "text-success",
  failed: "text-error",
  error: "text-warning",
  queued: "text-muted",
  running: "text-muted",
};

export default async function ProjectPage() {
  const projects = await api<Page<Project>>("/projects/", "/project");
  const project = projects?.results[0] ?? null;
  const checks = project ? await api<Page<CheckRun>>(`/projects/${project.id}/checks/`, "/project") : null;

  return (
    <div className="mx-auto max-w-4xl">
      <Label tone="muted">Your project</Label>
      <h1 className="mt-2 font-display text-4xl font-bold tracking-[-0.03em] sm:text-5xl">
        {project?.name ?? "Create your project"}
      </h1>
      <p className="mt-3 max-w-2xl text-body">
        This is the product you&rsquo;re shipping. Checks run against it, and when it&rsquo;s live, this is what goes
        on your launch card.
      </p>

      <div className="mt-10 grid gap-8 lg:grid-cols-[1.3fr_1fr]">
        <ProjectForm project={project} />
        {project && <TokenBox token={project.ownership_token} />}
      </div>

      {project && (
        <section className="mt-14" aria-labelledby="history">
          <h2 id="history" className="font-display text-2xl font-bold">
            Check history
          </h2>
          {checks && checks.results.length > 0 ? (
            <ul className="mt-4 divide-y divide-line border-y border-line">
              {checks.results.map((run) => (
                <li key={run.id} className="flex flex-wrap items-center gap-x-6 gap-y-1 py-3 text-sm">
                  <span className={`w-16 font-mono text-xs font-semibold uppercase ${STATUS_STYLE[run.status]}`}>{run.status}</span>
                  <span className="font-semibold">{run.step.replace(/-/g, " ")}</span>
                  <span className="flex-1 truncate text-muted">{run.result.reasons?.[0] ?? run.result.checked ?? ""}</span>
                  <time className="font-mono text-xs text-muted" dateTime={run.created} title={new Date(run.created).toUTCString()}>
                    {new Date(run.created).toISOString().slice(0, 16).replace("T", " ")} UTC
                  </time>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-4 border-2 border-dashed border-line p-6 text-center text-muted">
              Nothing checked yet. Your first &ldquo;Check my work&rdquo; shows up here.
            </p>
          )}
        </section>
      )}
    </div>
  );
}
