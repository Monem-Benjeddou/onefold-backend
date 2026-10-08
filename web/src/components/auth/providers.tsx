import { GitHubIcon, GoogleIcon } from "@/components/icons";
import { buttonClass } from "@/components/button";

const LABELS = { github: "GitHub", google: "Google" } as const;

/** "Continue with GitHub / Google". Rendered only for providers the API has keys for. */
export function ProviderButtons({ providers, next }: { providers: ("github" | "google")[]; next?: string }) {
  if (!providers.length) return null;
  const query = next ? `?next=${encodeURIComponent(next)}` : "";
  return (
    <div className="grid gap-3">
      {providers.map((provider) => (
        <a
          key={provider}
          href={`/api/auth/oauth/${provider}/start${query}`}
          className={buttonClass("secondary", "w-full bg-elevated hover:bg-surface hover:text-ink")}
        >
          {provider === "github" ? <GitHubIcon /> : <GoogleIcon />}
          Continue with {LABELS[provider]}
        </a>
      ))}
    </div>
  );
}

export function Divider({ children = "or" }: { children?: string }) {
  return (
    <div className="my-6 flex items-center gap-4 font-mono text-xs uppercase tracking-[0.12em] text-muted" role="separator">
      <span className="h-px flex-1 bg-line" />
      {children}
      <span className="h-px flex-1 bg-line" />
    </div>
  );
}
