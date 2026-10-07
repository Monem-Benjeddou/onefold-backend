"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/button";
import { Label } from "@/components/label";
import { ApiError, call } from "@/lib/client";
import type { CheckRun, Enrollment, Project, StepDetail } from "@/lib/types";

const POLL_MS = 1000;
const POLL_LIMIT = 45;

function describeCheck(step: StepDetail, project: Project | null) {
  const check = step.check;
  if (!check) return null;
  if (check.kind === "attest") return `You confirm: ${check.statement}`;
  if (check.kind === "http.get" && check.url) {
    const url = check.url.replace("{project.live_url}", project?.live_url || "<your live URL>");
    const wants = check.expect_body_contains ? " and your verification token in the response" : "";
    return `We call GET ${url} and expect status ${check.expect_status ?? 200}${wants}. We don't follow redirects.`;
  }
  return "We run this step's check against your project.";
}

export function StepActions({ step, project }: { step: StepDetail; project: Project | null }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [run, setRun] = useState<CheckRun | null>(null);
  const [status, setStatus] = useState(step.status);
  const mounted = useRef(true);

  // Opening a step starts it, and Continue later resumes at the same scroll position.
  useEffect(() => {
    mounted.current = true;
    if (step.status === "available") {
      call(`/learning/enrollment/steps/${step.slug}/start/`, { method: "POST" })
        .then(() => setStatus("in_progress"))
        .catch(() => undefined);
    }
    if (step.last_position > 0) window.scrollTo({ top: step.last_position });

    let timer: ReturnType<typeof setTimeout> | undefined;
    const save = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        call(`/learning/enrollment/steps/${step.slug}/`, {
          method: "PATCH",
          body: { last_position: Math.round(window.scrollY) },
        }).catch(() => undefined);
      }, 1200);
    };
    window.addEventListener("scroll", save, { passive: true });
    return () => {
      mounted.current = false;
      clearTimeout(timer);
      window.removeEventListener("scroll", save);
    };
  }, [step.slug, step.status, step.last_position]);

  const goNext = useCallback(async () => {
    const enrollment = await call<Enrollment>("/learning/enrollment/");
    router.push(enrollment.next_step ? `/steps/${enrollment.next_step.slug}` : "/ship");
    router.refresh();
  }, [router]);

  async function markDone() {
    setBusy(true);
    setError(null);
    try {
      await call(`/learning/enrollment/steps/${step.slug}/complete/`, { method: "POST" });
      setStatus("done");
      await goNext();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't save. Try again.");
      setBusy(false);
    }
  }

  async function checkWork() {
    if (!project) return;
    setBusy(true);
    setError(null);
    setRun(null);
    try {
      let current = await call<CheckRun>(`/projects/${project.id}/checks/`, {
        method: "POST",
        body: { step: step.slug },
        headers: { "Idempotency-Key": crypto.randomUUID() },
      });
      setRun(current);
      for (let i = 0; i < POLL_LIMIT && ["queued", "running"].includes(current.status); i++) {
        await new Promise((resolve) => setTimeout(resolve, POLL_MS));
        if (!mounted.current) return;
        current = await call<CheckRun>(`/checks/${current.id}/`);
        setRun(current);
      }
      if (current.status === "passed") {
        setStatus("done");
        if (step.type === "ship") {
          router.push("/ship");
          return;
        }
        router.refresh();
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't reach Onefold. Try again.");
    }
    setBusy(false);
  }

  const finished = status === "done" || status === "skipped";
  const checkText = describeCheck(step, project);
  const needsLiveUrl = step.check?.kind === "http.get" && !project?.live_url;

  return (
    <aside className="lg:sticky lg:top-12 lg:self-start" aria-label="Step actions">
      <div className="border-2 border-ink bg-elevated p-6 shadow-hard">
        {status === "locked" ? (
          <>
            <Label tone="muted">Locked</Label>
            <p className="mt-3">Finish the previous step first. You can read ahead.</p>
            <Link href="/home" className="mt-5 inline-block font-semibold underline underline-offset-4">
              Back to your next step
            </Link>
          </>
        ) : finished ? (
          <>
            <Label tone="patina">✓ Done</Label>
            <p className="mt-3">This step is complete.</p>
            <Button className="mt-5 w-full" onClick={goNext}>
              Next step →
            </Button>
          </>
        ) : step.has_check ? (
          <>
            <Label>{step.type === "ship" ? "Ship it" : "Check my work"}</Label>
            <p className="mt-3 text-sm leading-relaxed text-body">{checkText}</p>
            {!project ? (
              <p className="mt-5 text-sm">
                Checks run against your project.{" "}
                <Link href="/project" className="font-semibold underline underline-offset-4">
                  Create it first
                </Link>
                .
              </p>
            ) : needsLiveUrl ? (
              <p className="mt-5 text-sm">
                Add your live URL and put your token in <code className="font-mono">/health</code>.{" "}
                <Link href="/project" className="font-semibold underline underline-offset-4">
                  Open project settings
                </Link>
                .
              </p>
            ) : (
              <Button className="mt-5 w-full" onClick={checkWork} disabled={busy}>
                {busy ? "Checking…" : step.check?.kind === "attest" ? "I confirm, check it" : "Check my work"}
              </Button>
            )}
          </>
        ) : (
          <>
            <Label>When you&rsquo;re done</Label>
            <p className="mt-3 text-sm text-body">No check on this one. Mark it done and keep moving.</p>
            <Button className="mt-5 w-full" onClick={markDone} disabled={busy}>
              {busy ? "Saving…" : "Mark as done"}
            </Button>
          </>
        )}
        {error && (
          <p role="alert" className="mt-4 text-sm font-medium text-error">
            ⚠ {error}
          </p>
        )}
      </div>

      {run && <CheckResult run={run} />}
    </aside>
  );
}

function CheckResult({ run }: { run: CheckRun }) {
  const pending = run.status === "queued" || run.status === "running";
  const tone =
    run.status === "passed"
      ? "border-success"
      : run.status === "failed"
        ? "border-error"
        : run.status === "error"
          ? "border-warning"
          : "border-line";
  const heading = {
    queued: "Queued…",
    running: "Running…",
    passed: "✓ Passed",
    failed: "✕ Not yet",
    error: "⚠ Couldn't run the check",
  }[run.status];
  const got = run.result.got ?? {};

  return (
    <section className={`mt-6 border-2 ${tone} bg-elevated p-5`} aria-live="polite">
      <p className="font-display text-lg font-bold">{heading}</p>
      {pending && <p className="mt-1 text-sm text-muted">This usually takes a few seconds.</p>}
      {run.result.checked && (
        <div className="mt-3">
          <Label tone="muted">What we checked</Label>
          <p className="mt-1 text-sm">{run.result.checked}</p>
        </div>
      )}
      {"status" in got && (
        <div className="mt-3">
          <Label tone="muted">What we got</Label>
          <p className="mt-1 font-mono text-xs">
            {String(got.status)} {String(got.reason ?? "")} · {String(got.elapsed_ms ?? "?")} ms
          </p>
          {typeof got.body_excerpt === "string" && got.body_excerpt && (
            <pre className="mt-2 max-h-32 overflow-auto bg-carbon p-3 font-mono text-xs text-patina-light">{got.body_excerpt}</pre>
          )}
        </div>
      )}
      {!!run.result.reasons?.length && (
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
          {run.result.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
      {!!run.result.hints?.length && (
        <div className="mt-3 border-l-4 border-orange bg-surface px-3 py-2">
          <Label tone="muted">Try this</Label>
          {run.result.hints.map((hint) => (
            <p key={hint} className="mt-1 text-sm">
              {hint}
            </p>
          ))}
        </div>
      )}
    </section>
  );
}
