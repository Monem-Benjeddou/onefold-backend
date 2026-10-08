import type { CheckStatus, StepStatus } from "@/lib/types";

import { AlertIcon, CheckIcon, CrossIcon, LockIcon } from "./icons";

type Status = StepStatus | CheckStatus;

const STYLES: Record<Status, { text: string; className: string; icon?: React.ReactNode }> = {
  done: { text: "Done", className: "bg-patina-light text-patina", icon: <CheckIcon size={12} /> },
  skipped: { text: "Skipped", className: "bg-surface text-muted" },
  in_progress: { text: "In progress", className: "bg-orange-light text-ink" },
  available: { text: "Up next", className: "bg-orange-light text-ink" },
  locked: { text: "Locked", className: "bg-surface text-muted", icon: <LockIcon size={12} /> },
  queued: { text: "Queued", className: "bg-surface text-muted" },
  running: { text: "Running", className: "bg-surface text-ink" },
  passed: { text: "Passed", className: "bg-patina-light text-patina", icon: <CheckIcon size={12} /> },
  failed: { text: "Failed", className: "bg-[#fdf0f1] text-error", icon: <CrossIcon size={12} /> },
  error: { text: "Couldn't run", className: "bg-[#fbf4e4] text-warning", icon: <AlertIcon size={12} /> },
};

/** Status as icon + word (never colour alone). */
export function StatusPill({ status, className = "" }: { status: Status; className?: string }) {
  const style = STYLES[status];
  return (
    <span
      className={`inline-flex items-center gap-1 whitespace-nowrap px-2 py-0.5 font-mono text-[0.68rem] font-semibold uppercase tracking-[0.08em] ${style.className} ${className}`}
    >
      {style.icon}
      {style.text}
    </span>
  );
}
