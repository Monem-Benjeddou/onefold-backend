import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cache } from "react";

import { ArrowLeftIcon, ArrowRightIcon } from "@/components/icons";
import { Label } from "@/components/label";
import { Markdown } from "@/components/markdown";
import { StatusPill } from "@/components/status-pill";
import { api, getWorkspace } from "@/lib/api";
import type { StepDetail } from "@/lib/types";

import { StepActions } from "./step-actions";

type Props = { params: Promise<{ slug: string }> };

const getStep = cache((slug: string) =>
  api<StepDetail>(`/learning/enrollment/steps/${encodeURIComponent(slug)}/`, `/steps/${slug}`),
);

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const step = await getStep((await params).slug);
  return { title: step?.title ?? "Step" };
}

const TYPE_TEXT = { learn: "Read", build: "Build", check: "Check", ship: "Ship" } as const;

export default async function StepPage({ params }: Props) {
  const { slug } = await params;
  const [step, workspace] = await Promise.all([getStep(slug), getWorkspace()]);
  if (!step) notFound();

  return (
    <div className="mx-auto grid max-w-6xl gap-10 pb-24 lg:grid-cols-[minmax(0,1fr)_340px] lg:pb-0">
      <article className="min-w-0">
        <nav aria-label="Breadcrumb" className="font-mono text-xs uppercase tracking-[0.12em] text-muted">
          <Link href="/path" className="hover:text-ink hover:underline">
            Path
          </Link>{" "}
          / Station {String(step.station.order).padStart(2, "0")} · {step.station.title}
        </nav>
        <h1 className="mt-4 font-display text-4xl font-bold leading-tight tracking-[-0.03em] sm:text-5xl">{step.title}</h1>
        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 font-mono text-xs uppercase tracking-[0.1em] text-muted">
          <StatusPill status={step.status} />
          <span>{TYPE_TEXT[step.type]}</span>
          <span>About {step.est_minutes} min</span>
          <span>Role: {step.station.role}</span>
          {step.requires_laptop && <span>Best on a laptop</span>}
        </div>
        <div className="mt-10">
          <Markdown>{step.body_md}</Markdown>
        </div>

        <nav aria-label="Steps" className="mt-16 grid gap-4 border-t-2 border-ink pt-6 sm:grid-cols-2">
          {step.previous ? (
            <Link href={`/steps/${step.previous.slug}`} className="group flex min-h-16 flex-col justify-center border border-line bg-surface px-4 py-3 hover:border-ink">
              <span className="flex items-center gap-1.5 font-mono text-[0.7rem] uppercase tracking-[0.1em] text-muted">
                <ArrowLeftIcon size={13} /> Previous
              </span>
              <span className="mt-1 font-semibold group-hover:underline">{step.previous.title}</span>
            </Link>
          ) : (
            <span />
          )}
          {step.next && (
            <Link
              href={`/steps/${step.next.slug}`}
              className="group flex min-h-16 flex-col justify-center border border-line bg-surface px-4 py-3 text-right hover:border-ink"
            >
              <span className="flex items-center justify-end gap-1.5 font-mono text-[0.7rem] uppercase tracking-[0.1em] text-muted">
                Next{step.next.status === "locked" ? " · read ahead" : ""} <ArrowRightIcon size={13} />
              </span>
              <span className="mt-1 font-semibold group-hover:underline">{step.next.title}</span>
            </Link>
          )}
        </nav>
      </article>
      <StepActions step={step} project={workspace.project} />
    </div>
  );
}
