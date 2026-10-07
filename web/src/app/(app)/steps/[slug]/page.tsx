import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Label } from "@/components/label";
import { Markdown } from "@/components/markdown";
import { api } from "@/lib/api";
import type { Page, Project, StepDetail } from "@/lib/types";

import { StepActions } from "./step-actions";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  return { title: slug.replace(/-/g, " ") };
}

const TYPE_TEXT = { learn: "Learn", build: "Build", check: "Check", ship: "Ship" } as const;

export default async function StepPage({ params }: Props) {
  const { slug } = await params;
  const here = `/steps/${slug}`;
  const [step, projects] = await Promise.all([
    api<StepDetail>(`/learning/enrollment/steps/${encodeURIComponent(slug)}/`, here),
    api<Page<Project>>("/projects/", here),
  ]);
  if (!step) notFound();
  const project = projects?.results[0] ?? null;

  return (
    <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[1fr_340px]">
      <article>
        <Label>
          Station {String(step.station.order).padStart(2, "0")} · {step.station.title} · {step.station.role}
        </Label>
        <h1 className="mt-3 font-display text-4xl font-bold leading-tight tracking-[-0.03em] sm:text-5xl">{step.title}</h1>
        <p className="mt-4 flex flex-wrap gap-x-5 gap-y-1 font-mono text-xs uppercase tracking-[0.1em] text-muted">
          <span>{TYPE_TEXT[step.type]}</span>
          <span>About {step.est_minutes} min</span>
          {step.requires_laptop && <span>Best on a laptop</span>}
        </p>
        <div className="mt-10">
          <Markdown>{step.body_md}</Markdown>
        </div>
      </article>
      <StepActions step={step} project={project} />
    </div>
  );
}
