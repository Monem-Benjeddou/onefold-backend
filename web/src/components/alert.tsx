import type { ReactNode } from "react";

import { AlertIcon, CheckIcon, CrossIcon, InfoIcon } from "./icons";

type Tone = "error" | "success" | "info" | "warning";

const tones: Record<Tone, { box: string; icon: ReactNode }> = {
  error: { box: "border-error bg-[#fdf0f1] text-ink", icon: <CrossIcon className="text-error" /> },
  success: { box: "border-success bg-[#eef7f1] text-ink", icon: <CheckIcon className="text-success" /> },
  info: { box: "border-ink bg-surface text-ink", icon: <InfoIcon className="text-info" /> },
  warning: { box: "border-warning bg-[#fbf4e4] text-ink", icon: <AlertIcon className="text-warning" /> },
};

/** A status message: icon + words, never colour alone. */
export function Alert({
  tone = "info",
  title,
  children,
  className = "",
  id,
  role,
  tabIndex,
}: {
  tone?: Tone;
  title?: ReactNode;
  children?: ReactNode;
  className?: string;
  id?: string;
  role?: "alert" | "status";
  tabIndex?: number;
}) {
  const { box, icon } = tones[tone];
  return (
    <div
      id={id}
      role={role ?? (tone === "error" ? "alert" : "status")}
      tabIndex={tabIndex}
      className={`flex gap-3 border-l-4 px-4 py-3 text-sm leading-relaxed outline-none ${box} ${className}`}
    >
      <span className="mt-0.5 shrink-0">{icon}</span>
      <div className="min-w-0">
        {title && <p className="font-semibold">{title}</p>}
        {children && <div className={title ? "mt-0.5 text-body" : ""}>{children}</div>}
      </div>
    </div>
  );
}
