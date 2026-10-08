"use client";

import type { ReactNode } from "react";

import { CheckIcon } from "./icons";

export type CardOption = { value: string; title: ReactNode; body?: ReactNode; extra?: ReactNode };

/** A radio group drawn as cards. Native radios underneath: arrow keys and screen readers just work. */
export function RadioCards({
  name,
  legend,
  options,
  value,
  onChange,
  columns = "sm:grid-cols-3",
}: {
  name: string;
  legend: string;
  options: CardOption[];
  value: string;
  onChange: (value: string) => void;
  columns?: string;
}) {
  return (
    <fieldset className={`grid gap-4 ${columns}`}>
      <legend className="sr-only">{legend}</legend>
      {options.map((option) => {
        const checked = value === option.value;
        return (
          <label
            key={option.value}
            className={`relative flex cursor-pointer flex-col border-2 border-ink p-5 transition-[box-shadow,background-color] has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-orange ${
              checked ? "bg-elevated shadow-hard-orange" : "bg-surface hover:bg-elevated"
            }`}
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={checked}
              onChange={() => onChange(option.value)}
              className="sr-only"
            />
            <span
              aria-hidden="true"
              className={`absolute right-4 top-4 flex h-5 w-5 items-center justify-center border-2 border-ink ${checked ? "bg-orange" : "bg-elevated"}`}
            >
              {checked && <CheckIcon size={12} strokeWidth={3.5} />}
            </span>
            <span className="block pr-8 font-semibold">{option.title}</span>
            {option.body && <span className="mt-1.5 block text-sm leading-relaxed text-muted">{option.body}</span>}
            {option.extra}
          </label>
        );
      })}
    </fieldset>
  );
}
