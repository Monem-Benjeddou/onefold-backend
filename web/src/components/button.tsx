import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

import { Spinner } from "./spinner";

type Variant = "primary" | "secondary" | "ghost" | "inverse" | "dark" | "danger";

const base =
  "inline-flex items-center justify-center gap-2 px-5 py-3 text-[0.95rem] font-semibold transition-[transform,box-shadow,background-color,color] duration-150 ease-out disabled:cursor-not-allowed disabled:opacity-50 aria-disabled:cursor-not-allowed aria-disabled:opacity-50 min-h-11 select-none";

const variants: Record<Variant, string> = {
  // One Orange action per screen, with the hard shadow.
  primary:
    // Hover deepens the shadow without moving the button (moving it can slide it
    // out from under the cursor and make it flicker); pressing pushes it in.
    "bg-orange text-ink border-2 border-ink shadow-hard hover:shadow-[8px_8px_0_0_var(--color-ink)] active:translate-x-1 active:translate-y-1 active:shadow-none disabled:shadow-none",
  secondary: "border-2 border-ink text-ink bg-transparent hover:bg-ink hover:text-paper",
  ghost: "text-ink underline-offset-4 hover:underline px-2",
  // For Orange or Brass grounds, where white-on-orange would fail contrast.
  dark: "bg-ink text-paper border-2 border-ink hover:bg-carbon-3",
  inverse:
    "bg-orange text-ink border-2 border-paper shadow-hard-paper hover:shadow-[8px_8px_0_0_var(--color-paper)] active:translate-x-1 active:translate-y-1 active:shadow-none",
  danger: "border-2 border-error text-error bg-transparent hover:bg-error hover:text-paper",
};

export function buttonClass(variant: Variant = "primary", extra = "") {
  return `${base} ${variants[variant]} ${extra}`;
}

export function Button({
  variant = "primary",
  className = "",
  loading = false,
  loadingText,
  children,
  disabled,
  ...props
}: ComponentProps<"button"> & { variant?: Variant; loading?: boolean; loadingText?: string }) {
  return (
    <button
      className={buttonClass(variant, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? (
        <>
          <Spinner />
          <span>{loadingText ?? children}</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}

export function ButtonLink({
  href,
  variant = "primary",
  className = "",
  children,
  prefetch,
}: {
  href: string;
  variant?: Variant;
  className?: string;
  children: ReactNode;
  prefetch?: boolean;
}) {
  return (
    <Link href={href} className={buttonClass(variant, className)} prefetch={prefetch}>
      {children}
    </Link>
  );
}
