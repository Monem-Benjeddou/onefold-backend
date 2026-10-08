"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Alert } from "@/components/alert";
import { Button } from "@/components/button";
import { Field, Input, Textarea } from "@/components/field";
import { useToast } from "@/components/toast";
import { ApiError, call } from "@/lib/client";
import type { Project } from "@/lib/types";

type Fields = Pick<Project, "name" | "idea" | "repo_full_name" | "live_url">;
const KEYS = ["name", "idea", "repo_full_name", "live_url"] as const;

export function ProjectForm({ project }: { project: Project | null }) {
  const router = useRouter();
  const toast = useToast();
  const initial: Fields = {
    name: project?.name ?? "",
    idea: project?.idea ?? "",
    repo_full_name: project?.repo_full_name ?? "",
    live_url: project?.live_url ?? "",
  };
  const [fields, setFields] = useState<Fields>(initial);
  const [saved, setSaved] = useState<Fields>(initial);
  const [errors, setErrors] = useState<Partial<Record<keyof Fields | "form", string>>>({});
  const [busy, setBusy] = useState(false);
  const dirty = KEYS.some((key) => fields[key] !== saved[key]);

  const set = (key: keyof Fields) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFields({ ...fields, [key]: event.target.value });
    setErrors({ ...errors, [key]: undefined });
  };

  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (!fields.name.trim()) return setErrors({ name: "Give your project a name." });
    setBusy(true);
    setErrors({});
    try {
      const result = await call<Project>(project ? `/projects/${project.id}/` : "/projects/", {
        method: project ? "PATCH" : "POST",
        body: fields,
      });
      const next = { name: result.name, idea: result.idea, repo_full_name: result.repo_full_name, live_url: result.live_url };
      setFields(next);
      setSaved(next);
      toast("Project saved.");
      router.refresh();
    } catch (e) {
      const fieldErrors = e instanceof ApiError ? e.fields : {};
      const found: typeof errors = {};
      for (const key of KEYS) if (fieldErrors[key]) found[key] = fieldErrors[key];
      if (!Object.keys(found).length) found.form = e instanceof Error ? e.message : "Couldn't save.";
      setErrors(found);
    }
    setBusy(false);
  }

  return (
    <form onSubmit={save} className="space-y-5" noValidate>
      <Field label="Name" error={errors.name}>
        {(a11y) => <Input {...a11y} value={fields.name} onChange={set("name")} required maxLength={80} placeholder="Habit Loop" />}
      </Field>
      <Field label="The idea" optional error={errors.idea} hint={`Who struggles to do what, and why. ${fields.idea.length}/280`}>
        {(a11y) => <Textarea {...a11y} value={fields.idea} onChange={set("idea")} maxLength={280} rows={3} />}
      </Field>
      <Field label="GitHub repository" optional error={errors.repo_full_name} hint="owner/repo, or paste the GitHub URL.">
        {(a11y) => (
          <Input {...a11y} value={fields.repo_full_name} onChange={set("repo_full_name")} placeholder="ada/habit-loop" spellCheck={false} autoCapitalize="none" />
        )}
      </Field>
      <Field label="Live URL" optional error={errors.live_url} hint="Your deployed app, https only. Needed for the Deploy station.">
        {(a11y) => (
          <Input
            {...a11y}
            type="url"
            inputMode="url"
            value={fields.live_url}
            onChange={set("live_url")}
            placeholder="https://habit-loop.example.com"
            spellCheck={false}
            autoCapitalize="none"
          />
        )}
      </Field>
      {errors.form && <Alert tone="error">{errors.form}</Alert>}
      <div className="flex flex-wrap items-center gap-4">
        <Button type="submit" loading={busy} loadingText="Saving…" disabled={!dirty}>
          {project ? "Save changes" : "Create project"}
        </Button>
        {dirty && !busy && <span className="text-sm text-muted">Unsaved changes</span>}
      </div>
    </form>
  );
}
