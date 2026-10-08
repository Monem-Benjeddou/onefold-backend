"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { Alert } from "@/components/alert";
import { Button, ButtonLink } from "@/components/button";
import { ArrowRightIcon, LockIcon } from "@/components/icons";
import { Label } from "@/components/label";
import { useToast } from "@/components/toast";
import { ApiError, call } from "@/lib/client";
import type { CheckRun, Enrollment, Project, StepDetail } from "@/lib/types";

/** Poll quickly at first, then back off: most checks finish in a few seconds. */
const POLL_DELAYS = [700, 1000, 1000, 1500, 2000, 2000, 3000, 3000, 5000];
const POLL_LIMIT_MS = 90_000;

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
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [run, setRun] = useState<CheckRun | null>(null);
  const [status, setStatus] = useState(step.status);
  const mounted = useRef(true);
  const resultRef = useRef<HTMLDivElement>(null);

  // Opening a step starts it, and Continue later resumes at the same scroll position.
  useEffect(() => {
    mounted.current = true;
    if (step.status === "available") {
      call(`/learning/enrollment/steps/${step.slug}/start/`, { method: "POST" })
        .then(() => mounted.current && setStatus("in_progress"))
        .catch(() => undefined);
    }
    if (step.last_position > 0) requestAnimationFrame(() => window.scrollTo({ top: step.last_position }));

    let timer: ReturnType<typeof setTimeout> | undefined;
    const save = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        if (step.status === "locked") return;
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
    const previous = status;
    setStatus("done"); // optimistic; rolled back below if the server says no
    try {
      await call(`/learning/enrollment/steps/${step.slug}/complete/`, { method: "POST" });
      toast("Step done. Next one unlocked.");
      await goNext();
    } catch (e) {
      setStatus(previous);
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
      const started = Date.now();
      for (let i = 0; ["queued", "running"].includes(current.status) && Date.now() - started < POLL_LIMIT_MS; i++) {
        await new Promise((resolve) => setTimeout(resolve, POLL_DELAYS[Math.min(i, POLL_DELAYS.length - 1)]));
        if (!mounted.current) return;
        current = await call<CheckRun>(`/checks/${current.id}/`);
        setRun(current);
      }
      requestAnimationFrame(() => resultRef.current?.focus());
      if (current.status === "passed") {
        setStatus("done");
        if (step.type === "ship") {
          router.push("/ship");
          return;
        }
        toast("Check passed. Next step unlocked.");
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

  // The one primary action for this step, shared by the side rail and the phone bar.
  let primary: React.ReactNode = null;
  if (status === "locked") {
    primary = (
      <ButtonLink href="/home" variant="secondary" className="w-full">
        Go to your current step
      </ButtonLink>
    );
  } else if (finished) {
    primary = (
      <Button className="w-full" onClick={goNext}>
        Next step <ArrowRightIcon />
      </Button>
    );
  } else if (step.has_check) {
    primary =
      !project || needsLiveUrl ? (
        <ButtonLink href="/project" className="w-full">
          {needsLiveUrl ? "Add your live URL" : "Set up your project"}
        </ButtonLink>
      ) : (
        <Button className="w-full" onClick={checkWork} loading={busy} loadingText="Checking…">
          {step.check?.kind === "attest" ? "I confirm, check it" : step.type === "ship" ? "Check it's live" : "Check my work"}
        </Button>
      );
  } else {
    primary = (
      <Button className="w-full" onClick={markDone} loading={busy} loadingText="Saving…">
        Mark as done
      </Button>
    );
  }

  return (
    <>
      <aside className="lg:sticky lg:top-12 lg:self-start" aria-label="Step actions">
        <div className="border-2 border-ink bg-elevated p-6 shadow-hard">
          {status === "locked" ? (
            <>
              <Label tone="muted">
                <span className="inline-flex items-center gap-1.5">
                  <LockIcon size={13} /> Reading ahead
                </span>
              </Label>
              <p className="mt-3 text-sm leading-relaxed text-body">
                This step unlocks when you finish the ones before it. Read on; nothing here is wasted.
              </p>
            </>
          ) : finished ? (
            <>
              <Label tone="patina">✓ Done</Label>
              <p className="mt-3 text-sm text-body">This step is complete.</p>
            </>
          ) : step.has_check ? (
            <>
              <Label>{step.type === "ship" ? "Ship it" : "Check my work"}</Label>
              <p className="mt-3 text-sm leading-relaxed text-body">{checkText}</p>
              {!project && <p className="mt-3 text-sm">Checks run against your project. Set it up first.</p>}
              {needsLiveUrl && (
                <p className="mt-3 text-sm">
                  Add your live URL and return your token from <code className="font-mono">/health</code> in{" "}
                  <Link href="/project" className="font-semibold underline underline-offset-4">
                    project settings
                  </Link>
                  .
                </p>
              )}
            </>
          ) : (
            <>
              <Label>When you&rsquo;re done</Label>
              <p className="mt-3 text-sm text-body">No check on this one. Mark it done and keep moving.</p>
            </>
          )}
          <div className="mt-5 hidden lg:block">{primary}</div>
          {error && (
            <Alert tone="error" className="mt-4">
              {error}
            </Alert>
          )}
        </div>

        {run && (
          <div ref={resultRef} tabIndex={-1} className="outline-none">
            <CheckResult run={run} />
          </div>
        )}
      </aside>

      {/* Phones and tablets: the action stays in reach above the tab bar. */}
      <div className="fixed inset-x-0 bottom-16 z-20 border-t-2 border-ink bg-paper/95 px-4 py-3 backdrop-blur pb-[calc(0.75rem+env(safe-area-inset-bottom))] lg:hidden">
        {primary}
      </div>
    </>
  );
}

function CheckResult({ run }: { run: CheckRun }) {
  const pending = run.status === "queued" || run.status === "running";
  const tone =
    run.status === "passed" ? "border-success" : run.status === "failed" ? "border-error" : run.status === "error" ? "border-warning" : "border-line";
  const heading = {
    queued: "Queued…",
    running: "Running…",
    passed: "✓ Passed",
    failed: "✕ Not yet",
    error: "⚠ We couldn't run the check. That's on us, not you.",
  }[run.status];
  const got = run.result.got ?? {};

  return (
    <section className={`mt-6 border-2 ${tone} bg-elevated p-5`} aria-live="polite" aria-label="Check result">
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
