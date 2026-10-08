"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { Alert } from "@/components/alert";
import { Button } from "@/components/button";
import { Field, Input, Textarea } from "@/components/field";
import { ArrowLeftIcon, ArrowRightIcon, CheckIcon } from "@/components/icons";
import { Label } from "@/components/label";
import { RadioCards } from "@/components/radio-cards";
import { ApiError, call } from "@/lib/client";
import type { OnboardingDraft, OnboardingState } from "@/lib/types";

const STEPS = ["Idea", "Pace", "Experience", "Project"] as const;
const OWN = "own";

const PACE_TEXT: Record<string, string> = {
  "2-4": "Evenings and the odd weekend.",
  "5-8": "A steady side project.",
  "10+": "This is the main thing right now.",
};
const EXPERIENCE_TEXT: Record<string, string> = {
  never: "We'll explain each deploy step in full.",
  once: "Hints when it matters, room to work.",
  often: "Short hints. You know the drill.",
};

type SaveState = "idle" | "saving" | "saved" | "offline";

/** Which steps are answered: you can go back freely, but not skip ahead of an unanswered one. */
function furthestAllowed(draft: OnboardingDraft) {
  if (!draft.pace) return 2;
  if (!draft.experience) return 3;
  return 4;
}

export function Wizard({
  state,
  userId,
  firstName,
  requestedStep,
}: {
  state: OnboardingState;
  userId: string;
  firstName: string;
  requestedStep: number;
}) {
  const router = useRouter();
  const storageKey = `onefold-onboarding-${userId}`;
  const [draft, setDraft] = useState<OnboardingDraft>(() => ({ pace: "5-8", ...state.draft }));
  const [step, setStep] = useState(() => {
    const wanted = requestedStep || state.step || 1;
    return Math.min(Math.max(wanted, 1), furthestAllowed({ pace: "5-8", ...state.draft }));
  });
  const [save, setSave] = useState<SaveState>("idle");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [finishing, setFinishing] = useState<"no" | "busy" | "done">("no");
  const nameEdited = useRef(Boolean(state.draft.project_name));
  const heading = useRef<HTMLHeadingElement>(null);
  const welcomeBack = state.step > 1 && Object.keys(state.draft).length > 0;

  // A local copy too, in case the session ends before the server save lands.
  useEffect(() => {
    try {
      const local = JSON.parse(sessionStorage.getItem(storageKey) ?? "null") as OnboardingDraft | null;
      if (local) setDraft((current) => ({ ...current, ...local }));
    } catch {
      // Storage unavailable (private mode): the server draft is enough.
    }
  }, [storageKey]);

  // Keep the URL in step, so back/forward and refresh land on the same question.
  useEffect(() => {
    const url = `/onboarding?step=${step}`;
    if (window.location.pathname + window.location.search !== url) window.history.replaceState(null, "", url);
    heading.current?.focus();
  }, [step]);

  useEffect(() => {
    const onPop = () => {
      const wanted = Number(new URLSearchParams(window.location.search).get("step")) || 1;
      setStep(Math.min(Math.max(wanted, 1), 4));
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  // Autosave (debounced) on every change.
  const firstRender = useRef(true);
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(draft));
    } catch {}
    setSave("saving");
    const timer = setTimeout(() => {
      call("/onboarding/draft/", { method: "PUT", body: { step, data: draft } })
        .then(() => setSave("saved"))
        .catch(() => setSave("offline"));
    }, 600);
    return () => clearTimeout(timer);
  }, [draft, step, storageKey]);

  const update = useCallback((patch: OnboardingDraft) => {
    setDraft((current) => ({ ...current, ...patch }));
    setErrors({});
  }, []);

  function go(to: number) {
    window.history.pushState(null, "", `/onboarding?step=${to}`);
    setStep(to);
    window.scrollTo({ top: 0 });
  }

  function chooseStarter(slug: string) {
    const starter = state.starters.find((s) => s.slug === slug);
    const patch: OnboardingDraft = { starter: slug };
    if (!nameEdited.current) patch.project_name = starter ? starter.name : "";
    if (slug === OWN && !draft.project_idea) patch.project_idea = draft.idea ?? "";
    update(patch);
  }

  async function finish(event: React.FormEvent) {
    event.preventDefault();
    const found: Record<string, string> = {};
    if (!draft.starter) found.starter = "Pick a starter project, or your own idea.";
    if (!draft.project_name?.trim()) found.project_name = "Give it a working name.";
    if (draft.starter === OWN && !(draft.project_idea || draft.idea)?.trim()) {
      found.project_idea = "Describe your idea in a sentence. You can change it later.";
    }
    setErrors(found);
    if (Object.keys(found).length) return;

    setFinishing("busy");
    try {
      await call("/onboarding/", {
        method: "POST",
        body: {
          idea: draft.idea ?? "",
          pace: draft.pace,
          experience: draft.experience,
          starter: draft.starter,
          project_name: draft.project_name?.trim(),
          project_idea: draft.starter === OWN ? (draft.project_idea || draft.idea || "").trim() : "",
        },
      });
      try {
        sessionStorage.removeItem(storageKey);
      } catch {}
      setFinishing("done");
      router.replace("/home?welcome=1");
      router.refresh();
    } catch (error) {
      setFinishing("no");
      if (error instanceof ApiError && Object.keys(error.fields).length) setErrors(error.fields);
      else setErrors({ form: error instanceof Error ? error.message : "Couldn't finish. Your answers are saved; try again." });
    }
  }

  if (finishing === "done") {
    return (
      <div className="mx-auto flex max-w-3xl flex-col items-start px-4 pt-24 sm:px-6" role="status">
        <Label tone="patina">✓ All set</Label>
        <p className="mt-3 font-display text-4xl font-bold tracking-[-0.03em]">Setting up your build…</p>
      </div>
    );
  }

  const title = "mt-3 font-display text-4xl font-bold leading-tight tracking-[-0.03em] outline-none sm:text-5xl";

  return (
    <div className="mx-auto max-w-3xl px-4 pb-24 pt-6 sm:px-6">
      <nav aria-label="Onboarding progress">
        <ol className="grid grid-cols-4 gap-1.5">
          {STEPS.map((label, index) => {
            const n = index + 1;
            const reachable = n <= furthestAllowed(draft) && n !== step;
            return (
              <li key={label}>
                <button
                  type="button"
                  disabled={!reachable}
                  onClick={() => go(n)}
                  aria-current={n === step ? "step" : undefined}
                  className="group block w-full text-left disabled:cursor-default"
                >
                  <span className={`block h-1.5 ${n < step ? "bg-patina" : n === step ? "bg-orange" : "bg-line"}`} />
                  <span
                    className={`mt-2 hidden font-mono text-[0.7rem] uppercase tracking-[0.1em] sm:block ${
                      n === step ? "text-ink" : "text-muted"
                    } ${reachable ? "group-hover:text-ink group-hover:underline" : ""}`}
                  >
                    {n}. {label}
                  </span>
                </button>
              </li>
            );
          })}
        </ol>
      </nav>
      <div className="mt-3 flex items-center justify-between font-mono text-xs text-muted">
        <span>
          Step {step} of {STEPS.length}
        </span>
        <span aria-live="polite">
          {save === "saving" ? "Saving…" : save === "saved" ? "✓ Saved" : save === "offline" ? "Not saved yet. We'll retry." : ""}
        </span>
      </div>

      {welcomeBack && step === state.step && (
        <Alert tone="info" className="mt-8">
          Welcome back{firstName ? `, ${firstName}` : ""}. Your answers are where you left them.
        </Alert>
      )}

      {step === 1 && (
        <form
          className="mt-10"
          onSubmit={(event) => {
            event.preventDefault();
            go(2);
          }}
        >
          <Label>Your idea</Label>
          <h1 ref={heading} tabIndex={-1} className={title}>
            What do you want to exist that doesn&rsquo;t yet?
          </h1>
          <p className="mt-3 text-body">One or two sentences. You can pick a starter project at the end instead.</p>
          <Field label="Your idea" optional className="mt-8" hint={`${(draft.idea ?? "").length}/280`}>
            {(a11y) => (
              <Textarea
                {...a11y}
                rows={3}
                maxLength={280}
                value={draft.idea ?? ""}
                onChange={(event) => update({ idea: event.target.value })}
                placeholder="An app that helps freelancers chase late invoices without being awkward."
                className="text-lg"
              />
            )}
          </Field>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Button type="submit">
              {draft.idea?.trim() ? "Continue" : "Skip for now"} <ArrowRightIcon />
            </Button>
          </div>
        </form>
      )}

      {step === 2 && (
        <form
          className="mt-10"
          onSubmit={(event) => {
            event.preventDefault();
            go(3);
          }}
        >
          <Label>Pace</Label>
          <h1 ref={heading} tabIndex={-1} className={title}>
            How much time can you give it?
          </h1>
          <p className="mt-3 text-body">We use this to pace reminders and estimates. You can change it later.</p>
          <div className="mt-8">
            <RadioCards
              name="pace"
              legend="Hours per week"
              value={draft.pace ?? ""}
              onChange={(pace) => update({ pace })}
              options={state.paces.map((pace) => ({ value: pace.value, title: pace.label, body: PACE_TEXT[pace.value] }))}
            />
          </div>
          <StepButtons onBack={() => go(1)} />
        </form>
      )}

      {step === 3 && (
        <form
          className="mt-10"
          onSubmit={(event) => {
            event.preventDefault();
            if (!draft.experience) return setErrors({ experience: "Pick the one closest to you." });
            go(4);
          }}
        >
          <Label>Experience</Label>
          <h1 ref={heading} tabIndex={-1} className={title}>
            Have you put anything on the internet before?
          </h1>
          <p className="mt-3 text-body">This only changes how much detail the hints give you. It never locks anything.</p>
          <div className="mt-8">
            <RadioCards
              name="experience"
              legend="Deploy experience"
              value={draft.experience ?? ""}
              onChange={(experience) => update({ experience })}
              options={state.experiences.map((option) => ({
                value: option.value,
                title: option.label,
                body: EXPERIENCE_TEXT[option.value],
              }))}
            />
          </div>
          {errors.experience && (
            <Alert tone="error" className="mt-6">
              {errors.experience}
            </Alert>
          )}
          <StepButtons onBack={() => go(2)} />
        </form>
      )}

      {step === 4 && (
        <form className="mt-10" onSubmit={finish} noValidate>
          <Label>Your project</Label>
          <h1 ref={heading} tabIndex={-1} className={title}>
            What are you shipping?
          </h1>
          <p className="mt-3 text-body">
            Pick a starter with a proven scope, or bring your own idea. Either way it&rsquo;s yours: your repo, your URL.
          </p>
          <div className="mt-8">
            <RadioCards
              name="starter"
              legend="Starter project"
              columns="sm:grid-cols-2"
              value={draft.starter ?? ""}
              onChange={chooseStarter}
              options={[
                ...state.starters.map((starter) => ({
                  value: starter.slug,
                  title: starter.name,
                  body: starter.summary,
                  extra: (
                    <span className="mt-3 flex flex-wrap gap-1.5">
                      {starter.builds.map((item) => (
                        <span key={item} className="bg-paper px-2 py-0.5 font-mono text-[0.68rem] text-body">
                          {item}
                        </span>
                      ))}
                    </span>
                  ),
                })),
                {
                  value: OWN,
                  title: "My own idea",
                  body: draft.idea?.trim() ? `"${draft.idea.trim()}"` : "Build the thing you actually want to exist.",
                },
              ]}
            />
          </div>
          {errors.starter && (
            <Alert tone="error" className="mt-6">
              {errors.starter}
            </Alert>
          )}

          {draft.starter && (
            <div className="mt-10 grid gap-6 border-t-2 border-ink pt-8">
              <Field label="Working name" error={errors.project_name} hint="Names change; shipped products stay.">
                {(a11y) => (
                  <Input
                    {...a11y}
                    maxLength={80}
                    value={draft.project_name ?? ""}
                    onChange={(event) => {
                      nameEdited.current = true;
                      update({ project_name: event.target.value });
                    }}
                    placeholder="Invoice Nudge"
                  />
                )}
              </Field>
              {draft.starter === OWN && (
                <Field
                  label="The idea in one sentence"
                  error={errors.project_idea}
                  hint={`Who struggles to do what, and why. ${(draft.project_idea ?? "").length}/280`}
                >
                  {(a11y) => (
                    <Textarea
                      {...a11y}
                      rows={3}
                      maxLength={280}
                      value={draft.project_idea ?? ""}
                      onChange={(event) => update({ project_idea: event.target.value })}
                    />
                  )}
                </Field>
              )}
            </div>
          )}

          {errors.form && (
            <Alert tone="error" className="mt-6" title="We couldn't finish setting up.">
              {errors.form}
            </Alert>
          )}
          {(errors.pace || errors.experience) && (
            <Alert tone="error" className="mt-6">
              {errors.pace ? "Go back to Pace and pick one." : "Go back to Experience and pick one."}
            </Alert>
          )}

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Button type="submit" loading={finishing === "busy"} loadingText="Setting up…">
              <CheckIcon /> Start building
            </Button>
            <button type="button" onClick={() => go(3)} className="inline-flex min-h-11 items-center gap-2 text-sm font-semibold underline-offset-4 hover:underline">
              <ArrowLeftIcon size={16} /> Back
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

function StepButtons({ onBack }: { onBack: () => void }) {
  return (
    <div className="mt-10 flex flex-wrap items-center gap-4">
      <Button type="submit">
        Continue <ArrowRightIcon />
      </Button>
      <button type="button" onClick={onBack} className="inline-flex min-h-11 items-center gap-2 text-sm font-semibold underline-offset-4 hover:underline">
        <ArrowLeftIcon size={16} /> Back
      </button>
    </div>
  );
}
