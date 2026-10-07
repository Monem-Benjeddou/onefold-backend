type Props = { size?: number; tone?: "ink" | "paper"; flap?: string; wordmark?: boolean; className?: string };

/** The Fold: a notched block with the flap folded into the corner. */
export function Symbol({ size = 28, tone = "ink", flap = "var(--color-orange)", className }: Omit<Props, "wordmark">) {
  const block = tone === "ink" ? "var(--color-ink)" : "var(--color-paper)";
  // Below 24px the flap is cut smaller so the gap never closes.
  const flapPath = size < 24 ? "M0 36L36 0V36Z" : "M0 40L40 0V40Z";
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" aria-hidden="true" className={className}>
      <path d="M48 0H100V100H0V48H48Z" fill={block} />
      <path d={flapPath} fill={flap} />
    </svg>
  );
}

export function Logo({ size = 28, tone = "ink", className = "" }: Props) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <Symbol size={size} tone={tone} />
      <span
        className={`font-display text-[1.45rem] font-extrabold leading-none tracking-[-0.04em] ${
          tone === "ink" ? "text-ink" : "text-paper"
        }`}
      >
        onefold
      </span>
    </span>
  );
}
