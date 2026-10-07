"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/button";
import { Label } from "@/components/label";
import { ApiError, call } from "@/lib/client";
import type { Page, Project } from "@/lib/types";

const PACES = [
  { value: "2-4", title: "2–4 hours a week", body: "Evenings and the odd weekend." },
  { value: "5-8", title: "5–8 hours a week", body: "A steady side project." },
  { value: "10+", title: "10+ hours a week", body: "This is the main thing right now." },
] as const;

const inputClass = "mt-3 block w-full border-2 border-ink bg-elevated px-4 py-3 text-lg outline-none focus:border-orange";

export function Wizard() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [idea, setIdea] = useState("");
  const [pace, setPace] = useState<(typeof PACES)[number]["value"]>("5-8");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function finish() {
    setBusy(true);
    setError(null);
    try {
      await call("/learning/enrollment/", { method: "POST", body: { pace } });
      // Safe to retry: only create the project if it isn't there yet.
      const existing = await call<Page<Project>>("/projects/");
      if (existing.count === 0) {
        await call("/projects/", { method: "POST", body: { name: name.trim(), idea: idea.trim() } });
      }
      router.push("/home");
      router.refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't save. Try again.");
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 pb-24 pt-8 sm:px-6">
      <div className="flex gap-1.5" aria-hidden="true">
        {[0, 1, 2].map((i) => (
          <span key={i} className={`h-1.5 flex-1 ${i < step ? "bg-patina" : i === step ? "bg-orange" : "bg-line"}`} />
        ))}
      </div>
      <p className="mt-3 font-mono text-xs text-muted">Question {step + 1} of 3</p>

      {step === 0 && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            setStep(1);
          }}
          className="mt-10"
        >
          <Label>No quiz about your experience</Label>
          <h1 className="mt-3 font-display text-4xl font-bold tracking-[-0.03em] sm:text-5xl">
            What do you want to exist that doesn&rsquo;t yet?
          </h1>
          <label htmlFor="idea" className="sr-only">
            Your idea
          </label>
          <textarea
            id="idea"
            autoFocus
            rows={3}
            maxLength={280}
            value={idea}
            onChange={(event) => setIdea(event.target.value)}
            className={`${inputClass} mt-8`}
            placeholder="An app that helps freelancers chase late invoices without being awkward."
          />
          <p className="mt-2 text-right font-mono text-xs text-muted">{idea.length}/280</p>
          <div className="mt-6 flex items-center gap-4">
            <Button type="submit" disabled={!idea.trim()}>
              Continue →
            </Button>
            <button type="button" onClick={() => setStep(1)} className="text-sm text-muted underline underline-offset-4">
              I&rsquo;ll decide later
            </button>
          </div>
        </form>
      )}

      {step === 1 && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            setStep(2);
          }}
          className="mt-10"
        >
          <Label>Pace</Label>
          <h1 className="mt-3 font-display text-4xl font-bold tracking-[-0.03em] sm:text-5xl">How much time can you give it?</h1>
          <fieldset className="mt-8 grid gap-4 sm:grid-cols-3">
            <legend className="sr-only">Hours per week</legend>
            {PACES.map((option) => (
              <label
                key={option.value}
                className={`cursor-pointer border-2 border-ink p-5 transition-shadow has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-orange ${
                  pace === option.value ? "bg-elevated shadow-hard-orange" : "bg-surface"
                }`}
              >
                <input
                  type="radio"
                  name="pace"
                  value={option.value}
                  checked={pace === option.value}
                  onChange={() => setPace(option.value)}
                  className="sr-only"
                />
                <span className="block font-semibold">{option.title}</span>
                <span className="mt-1 block text-sm text-muted">{option.body}</span>
              </label>
            ))}
          </fieldset>
          <p className="mt-4 text-sm text-muted">We use this to pace reminders. You can change it later.</p>
          <div className="mt-8 flex items-center gap-4">
            <Button type="submit">Continue →</Button>
            <button type="button" onClick={() => setStep(0)} className="text-sm underline underline-offset-4">
              Back
            </button>
          </div>
        </form>
      )}

      {step === 2 && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            finish();
          }}
          className="mt-10"
        >
          <Label>Your project</Label>
          <h1 className="mt-3 font-display text-4xl font-bold tracking-[-0.03em] sm:text-5xl">Give it a working name.</h1>
          <p className="mt-3 text-body">Don&rsquo;t overthink it. Names change; shipped products stay.</p>
          <label htmlFor="name" className="sr-only">
            Project name
          </label>
          <input
            id="name"
            autoFocus
            maxLength={80}
            value={name}
            onChange={(event) => setName(event.target.value)}
            className={`${inputClass} mt-8`}
            placeholder="Habit Loop"
          />
          {error && (
            <p role="alert" className="mt-4 text-sm font-medium text-error">
              ⚠ {error}
            </p>
          )}
          <div className="mt-8 flex items-center gap-4">
            <Button type="submit" disabled={busy || !name.trim()}>
              {busy ? "Setting up…" : "Start building →"}
            </Button>
            <button type="button" onClick={() => setStep(1)} className="text-sm underline underline-offset-4">
              Back
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
