import type { StepStatus } from "@/lib/types";

/** The Line: one segment per step. Done is Patina, current is Orange. */
export function Line({
  statuses,
  className = "",
  tone = "light",
  currentClass = "bg-orange",
}: {
  statuses: StepStatus[];
  className?: string;
  tone?: "light" | "dark";
  /** Override on Orange grounds, where an Orange segment would vanish. */
  currentClass?: string;
}) {
  const current = statuses.findIndex((s) => s === "in_progress" || s === "available");
  const done = statuses.filter((s) => s === "done" || s === "skipped").length;
  return (
    <div
      className={`flex gap-1 ${className}`}
      role="img"
      aria-label={`${done} of ${statuses.length} steps done`}
    >
      {statuses.map((status, index) => {
        const finished = status === "done" || status === "skipped";
        const color = finished
          ? "bg-patina"
          : index === current
            ? currentClass
            : tone === "dark"
              ? "bg-carbon-line"
              : "bg-line";
        return <span key={index} className={`h-2.5 flex-1 ${color}`} />;
      })}
    </div>
  );
}
