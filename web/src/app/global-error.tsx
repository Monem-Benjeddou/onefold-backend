"use client";

/** Last resort when even the root layout fails: plain HTML, no dependencies. */
export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#f3efe7", color: "#15120f" }}>
        <main style={{ padding: "15vh 24px", maxWidth: 640 }}>
          <h1 style={{ fontSize: 40, margin: 0 }}>Onefold didn&rsquo;t load.</h1>
          <p style={{ fontSize: 18, lineHeight: 1.6 }}>It&rsquo;s on us, not you. Try again in a moment.</p>
          <button
            onClick={reset}
            style={{ background: "#ff4f00", border: "2px solid #15120f", padding: "12px 20px", fontWeight: 600, fontSize: 16, cursor: "pointer" }}
          >
            Try again
          </button>
          {error.digest && <p style={{ fontFamily: "monospace", fontSize: 12, color: "#6a6358" }}>Reference: {error.digest}</p>}
        </main>
      </body>
    </html>
  );
}
