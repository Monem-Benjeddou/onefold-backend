"use client";

import { forwardRef, useId, useState, type ComponentProps, type ReactNode } from "react";

import { AlertIcon, CheckIcon, EyeIcon, EyeOffIcon } from "./icons";

export const inputClass =
  "block w-full border-2 border-ink bg-elevated px-4 py-3 text-base text-ink placeholder:text-muted/70 outline-none transition-colors focus:border-orange focus-visible:outline-none focus:shadow-[0_0_0_3px_var(--color-orange-light)] aria-[invalid=true]:border-error disabled:cursor-not-allowed disabled:bg-surface disabled:text-muted";

type FieldProps = {
  label: ReactNode;
  /** Shown under the input until there is an error. */
  hint?: ReactNode;
  error?: string | null;
  /** Content next to the label, e.g. a "Forgot password?" link. */
  aside?: ReactNode;
  optional?: boolean;
  children: (props: { id: string; "aria-invalid": boolean; "aria-describedby"?: string }) => ReactNode;
  className?: string;
};

/** Label + control + hint/error, wired for screen readers. */
export function Field({ label, hint, error, aside, optional, children, className = "" }: FieldProps) {
  const id = useId();
  const messageId = `${id}-message`;
  const hasMessage = Boolean(error || hint);
  return (
    <div className={className}>
      <div className="flex items-baseline justify-between gap-4">
        <label htmlFor={id} className="text-sm font-semibold text-ink">
          {label}
          {optional && <span className="ml-1.5 font-normal text-muted">(optional)</span>}
        </label>
        {aside}
      </div>
      <div className="mt-2">
        {children({ id, "aria-invalid": Boolean(error), "aria-describedby": hasMessage ? messageId : undefined })}
      </div>
      {error ? (
        <p id={messageId} className="mt-2 flex items-start gap-1.5 text-sm font-medium text-error">
          <AlertIcon size={15} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </p>
      ) : hint ? (
        <p id={messageId} className="mt-2 text-sm text-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export const Input = forwardRef<HTMLInputElement, ComponentProps<"input">>(function Input(
  { className = "", ...props },
  ref,
) {
  return <input ref={ref} className={`${inputClass} ${className}`} {...props} />;
});

export const Textarea = forwardRef<HTMLTextAreaElement, ComponentProps<"textarea">>(function Textarea(
  { className = "", ...props },
  ref,
) {
  return <textarea ref={ref} className={`${inputClass} resize-y ${className}`} {...props} />;
});

/** Password input with show/hide and a caps-lock warning. */
export const PasswordInput = forwardRef<HTMLInputElement, Omit<ComponentProps<"input">, "type">>(function PasswordInput(
  { className = "", onKeyDown, onKeyUp, onBlur, ...props },
  ref,
) {
  const [visible, setVisible] = useState(false);
  const [capsLock, setCapsLock] = useState(false);
  const detect = (event: React.KeyboardEvent<HTMLInputElement>) => setCapsLock(event.getModifierState?.("CapsLock") ?? false);
  return (
    <div>
      <div className="relative">
        <input
          ref={ref}
          type={visible ? "text" : "password"}
          spellCheck={false}
          autoCapitalize="none"
          className={`${inputClass} pr-14 ${className}`}
          onKeyDown={(event) => {
            detect(event);
            onKeyDown?.(event);
          }}
          onKeyUp={(event) => {
            detect(event);
            onKeyUp?.(event);
          }}
          onBlur={(event) => {
            setCapsLock(false);
            onBlur?.(event);
          }}
          {...props}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-muted hover:text-ink"
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
        >
          {visible ? <EyeOffIcon /> : <EyeIcon />}
        </button>
      </div>
      {capsLock && (
        <p className="mt-2 flex items-center gap-1.5 text-sm font-medium text-warning" role="status">
          <AlertIcon size={15} /> Caps Lock is on.
        </p>
      )}
    </div>
  );
});

export function Checkbox({ label, className = "", ...props }: Omit<ComponentProps<"input">, "type"> & { label: ReactNode }) {
  return (
    <label className={`inline-flex min-h-11 cursor-pointer items-center gap-3 text-sm ${className}`}>
      <input type="checkbox" className="peer sr-only" {...props} />
      <span
        aria-hidden="true"
        className="flex h-5 w-5 shrink-0 items-center justify-center border-2 border-ink bg-elevated text-transparent peer-checked:bg-orange peer-checked:text-ink peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-orange"
      >
        <CheckIcon size={14} strokeWidth={3} />
      </span>
      <span>{label}</span>
    </label>
  );
}
