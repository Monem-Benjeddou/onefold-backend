export type User = { id: string; email: string; name: string; created: string };

export type StepType = "learn" | "build" | "check" | "ship";
export type StepStatus = "locked" | "available" | "in_progress" | "done" | "skipped";

export type StepOutline = {
  slug: string;
  title: string;
  type: StepType;
  est_minutes: number;
  requires_laptop: boolean;
  has_check: boolean;
};

export type Station = {
  order: number;
  slug: string;
  title: string;
  role: string;
  steps: StepOutline[];
};

export type PathOutline = {
  slug: string;
  version: string;
  title: string;
  outcome: string;
  stations: Station[];
};

export type NextStep = {
  slug: string;
  title: string;
  type: StepType;
  est_minutes: number;
  station_order: number;
  station_title: string;
  status: StepStatus;
  last_position: number;
};

export type Enrollment = {
  id: string;
  status: "active" | "paused" | "shipped" | "abandoned";
  pace: "" | "2-4" | "5-8" | "10+";
  created: string;
  path: { slug: string; version: string; title: string; outcome: string };
  next_step: NextStep | null;
  steps: { slug: string; station: number; status: StepStatus; started_at: string | null; completed_at: string | null }[];
  totals: { done: number; total: number };
};

export type StepDetail = StepOutline & {
  body_md: string;
  station: { order: number; slug: string; title: string; role: string };
  check: {
    kind: "attest" | "http.get" | string;
    statement?: string;
    url?: string;
    expect_status?: number;
    expect_body_contains?: string;
  } | null;
  status: StepStatus;
  started_at: string | null;
  completed_at: string | null;
  last_position: number;
};

export type Project = {
  id: string;
  name: string;
  slug: string;
  idea: string;
  repo_full_name: string;
  live_url: string;
  visibility: "unlisted" | "public";
  ownership_token: string;
  enrollment: string | null;
  created: string;
  updated: string;
};

export type CheckStatus = "queued" | "running" | "passed" | "failed" | "error";

export type CheckRun = {
  id: string;
  project: string;
  step: string;
  kind: string;
  status: CheckStatus;
  result: {
    passed?: boolean;
    checked?: string;
    got?: Record<string, unknown>;
    reasons?: string[];
    hints?: string[];
  };
  duration_ms: number | null;
  created: string;
  started_at: string | null;
  finished_at: string | null;
};

export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };
