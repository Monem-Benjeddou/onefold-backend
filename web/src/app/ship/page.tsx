import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { ButtonLink } from "@/components/button";
import { Line } from "@/components/line";
import { Symbol } from "@/components/logo";
import { api, getWorkspace } from "@/lib/api";
import type { PathOutline } from "@/lib/types";

export const metadata: Metadata = { title: "It's live." };

/** The ship moment: only reachable once a Ship step has passed its check. */
export default async function ShipPage() {
  const [workspace, path] = await Promise.all([getWorkspace(), api<PathOutline>("/learning/paths/current/")]);
  const { enrollment, project } = workspace;
  if (!workspace.onboarding_complete || !enrollment || !path) redirect("/onboarding");

  const shipSlugs = path.stations.flatMap((s) => s.steps.filter((step) => step.type === "ship").map((step) => step.slug));
  const shipped = enrollment.steps.some((s) => shipSlugs.includes(s.slug) && s.status === "done");
  if (!shipped) redirect("/home");

  const next = enrollment.next_step;

  return (
    <main id="main" className="relative flex min-h-dvh flex-col justify-between overflow-hidden bg-[linear-gradient(135deg,var(--color-orange)_0%,var(--color-orange)_55%,var(--color-brass)_100%)] px-4 py-10 text-ink sm:px-10">
      <Symbol
        size={560}
        flap="var(--color-ink)"
        className="pointer-events-none absolute -bottom-24 -right-24 opacity-[0.12]"
      />
      <p className="relative font-mono text-xs uppercase tracking-[0.18em]">Deploy station · passed</p>

      <div className="relative max-w-4xl motion-safe:animate-[fold-in_420ms_ease-out]">
        <h1 className="font-display text-7xl font-extrabold leading-[0.85] tracking-[-0.05em] sm:text-9xl">It&rsquo;s live.</h1>
        {project?.live_url && (
          <a
            href={project.live_url}
            target="_blank"
            rel="noreferrer"
            className="mt-8 inline-block max-w-full truncate bg-ink px-5 py-3 font-mono text-paper hover:bg-carbon-3"
          >
            → {project.live_url.replace("https://", "")}
          </a>
        )}
        <p className="mt-8 max-w-xl text-xl leading-relaxed">
          {project?.idea ? <>It started as &ldquo;{project.idea.replace(/[.!?\s]+$/, "")}&rdquo;. </> : null}
          Now strangers can use it. Every role, done by you.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          {next ? (
            <ButtonLink href={`/steps/${next.slug}`} variant="dark">
              Next: {next.station_title} →
            </ButtonLink>
          ) : (
            <ButtonLink href="/home" variant="dark">
              Back to your dashboard
            </ButtonLink>
          )}
          <ButtonLink href="/project" variant="secondary">
            Project settings
          </ButtonLink>
        </div>
      </div>

      <div className="relative max-w-xl">
        <Line statuses={enrollment.steps.map((s) => s.status)} currentClass="bg-ink" />
        <p className="mt-2 font-mono text-xs">
          {enrollment.totals.done} of {enrollment.totals.total} steps
        </p>
      </div>
    </main>
  );
}
