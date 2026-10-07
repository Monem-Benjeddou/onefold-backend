"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/button";
import { ApiError, call } from "@/lib/client";
import type { Project } from "@/lib/types";

type Fields = Pick<Project, "name" | "idea" | "repo_full_name" | "live_url">;

const inputClass =
  "mt-2 block w-full border-2 border-ink bg-paper px-4 py-3 text-base outline-none focus:border-orange aria-[invalid=true]:border-error";

export function ProjectForm({ project }: { project: Project | null }) {
  const router = useRouter();
  const [fields, setFields] = useState<Fields>({
    name: project?.name ?? "",
    idea: project?.idea ?? "",
    repo_full_name: project?.repo_full_name ?? "",
    live_url: project?.live_url ?? "",
  });
  const [errors, setErrors] = useState<Partial<Record<keyof Fields | "form", string>>>({});
  const [state, setState] = useState<"idle" | "saving" | "saved">("idle");

  const set = (key: keyof Fields) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFields({ ...fields, [key]: event.target.value });
    setState("idle");
  };

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setState("saving");
    setErrors({});
    try {
      const saved = await call<Project>(project ? `/projects/${project.id}/` : "/projects/", {
        method: project ? "PATCH" : "POST",
        body: fields,
      });
      setFields({
        name: saved.name,
        idea: saved.idea,
        repo_full_name: saved.repo_full_name,
        live_url: saved.live_url,
      });
      setState("saved");
      router.refresh();
    } catch (e) {
      const data = e instanceof ApiError && e.data && typeof e.data === "object" ? (e.data as Record<string, string[]>) : {};
      const next: typeof errors = {};
      for (const key of ["name", "idea", "repo_full_name", "live_url"] as const) {
        if (data[key]) next[key] = data[key][0];
      }
      if (!Object.keys(next).length) next.form = e instanceof Error ? e.message : "Couldn't save.";
      setErrors(next);
      setState("idle");
    }
  }

  const field = (key: keyof Fields, label: string, props: React.InputHTMLAttributes<HTMLInputElement>, help?: string) => (
    <div>
      <label htmlFor={key} className="text-sm font-semibold">
        {label}
      </label>
      <input
        id={key}
        value={fields[key]}
        onChange={set(key)}
        aria-invalid={Boolean(errors[key])}
        aria-describedby={`${key}-help`}
        className={inputClass}
        {...props}
      />
      <p id={`${key}-help`} className={`mt-1.5 text-xs ${errors[key] ? "font-medium text-error" : "text-muted"}`}>
        {errors[key] ?? help}
      </p>
    </div>
  );

  return (
    <form onSubmit={save} className="space-y-5" noValidate>
      {field("name", "Name", { required: true, maxLength: 80, placeholder: "Habit Loop" })}
      <div>
        <label htmlFor="idea" className="text-sm font-semibold">
          The idea
        </label>
        <textarea
          id="idea"
          value={fields.idea}
          onChange={set("idea")}
          maxLength={280}
          rows={3}
          className={inputClass}
          placeholder="Who struggles to do what, and why."
        />
        <p className="mt-1.5 text-right font-mono text-xs text-muted">{fields.idea.length}/280</p>
      </div>
      {field("repo_full_name", "GitHub repository", { placeholder: "ada/habit-loop", spellCheck: false }, "owner/repo, or paste the GitHub URL.")}
      {field("live_url", "Live URL", { type: "url", placeholder: "https://habit-loop.example.com", spellCheck: false }, "Your deployed app, https only. Needed for the Deploy station.")}
      {errors.form && (
        <p role="alert" className="text-sm font-medium text-error">
          ⚠ {errors.form}
        </p>
      )}
      <div className="flex items-center gap-4">
        <Button type="submit" disabled={state === "saving" || !fields.name.trim()}>
          {state === "saving" ? "Saving…" : project ? "Save changes" : "Create project"}
        </Button>
        {state === "saved" && (
          <span role="status" className="text-sm font-semibold text-success">
            ✓ Saved
          </span>
        )}
      </div>
    </form>
  );
}
