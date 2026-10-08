"use client";

import { useState } from "react";

import { Label } from "@/components/label";

export function TokenBox({ token }: { token: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    await navigator.clipboard.writeText(token);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }
  return (
    <div className="self-start border-2 border-ink bg-carbon p-6 text-paper shadow-hard-orange">
      <Label tone="on-dark">Verification token</Label>
      <p className="mt-3 text-sm text-carbon-muted">
        Return this from <code className="font-mono text-paper">GET /health</code> on your live app. It proves the URL is
        yours.
      </p>
      <div className="mt-4 flex items-stretch">
        <code className="min-w-0 flex-1 truncate bg-carbon-3 px-3 py-2.5 font-mono text-xs text-patina-light">{token}</code>
        <button
          type="button"
          onClick={copy}
          className="shrink-0 border-l border-carbon-line bg-carbon-3 px-3 text-xs font-semibold hover:bg-carbon-line"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="mt-4 overflow-x-auto bg-carbon-2 p-3 font-mono text-[0.7rem] leading-relaxed text-carbon-muted">
{`// e.g. Express
app.get("/health", (req, res) =>
  res.json({ ok: true, token: "${token}" }));`}
      </pre>
    </div>
  );
}
