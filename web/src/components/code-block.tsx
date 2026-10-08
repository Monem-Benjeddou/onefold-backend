"use client";

import { useRef, useState } from "react";

import { CheckIcon, CopyIcon } from "./icons";

/** A code block with a copy button (used by the Markdown renderer). */
export function CodeBlock({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLPreElement>(null);
  const [copied, setCopied] = useState(false);

  async function copy() {
    const text = ref.current?.innerText ?? "";
    try {
      await navigator.clipboard.writeText(text.replace(/\n$/, ""));
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // Clipboard blocked (e.g. insecure context): leave the text selectable.
    }
  }

  return (
    <div className="group relative">
      <pre ref={ref}>{children}</pre>
      <button
        type="button"
        onClick={copy}
        className="absolute right-2 top-2 inline-flex items-center gap-1.5 bg-carbon-3 px-2.5 py-1.5 font-mono text-[0.7rem] text-paper opacity-90 hover:bg-carbon-line focus-visible:opacity-100"
        aria-label={copied ? "Copied" : "Copy code"}
      >
        {copied ? <CheckIcon size={13} /> : <CopyIcon size={13} />}
        {copied ? "Copied" : "Copy"}
      </button>
    </div>
  );
}
