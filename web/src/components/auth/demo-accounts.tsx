import type { DemoAccount } from "@/lib/types";

/** Development only (the API refuses otherwise): one click to sign in as a seeded account. */
export function DemoAccounts({ accounts, next }: { accounts: DemoAccount[]; next?: string }) {
  if (!accounts.length) return null;
  return (
    <section className="mt-10 border-2 border-dashed border-ink/40 p-4" aria-labelledby="demo-heading">
      <p id="demo-heading" className="font-mono text-[0.68rem] uppercase tracking-[0.12em] text-muted">
        Development · Sign in as
      </p>
      <ul className="mt-3 grid gap-2">
        {accounts.map((account) => (
          <li key={account.email}>
            <form action="/api/auth/demo" method="post">
              <input type="hidden" name="email" value={account.email} />
              {next && <input type="hidden" name="next" value={next} />}
              <button
                type="submit"
                className="flex min-h-11 w-full items-center justify-between gap-3 border border-line bg-elevated px-3 py-2 text-left text-sm hover:border-ink"
              >
                <span className="min-w-0">
                  <span className="block truncate font-semibold">{account.name || account.email.split("@")[0]}</span>
                  <span className="block truncate font-mono text-xs text-muted">{account.email}</span>
                </span>
                <span className="shrink-0 text-right text-xs text-body">{account.stage}</span>
              </button>
            </form>
          </li>
        ))}
      </ul>
    </section>
  );
}
