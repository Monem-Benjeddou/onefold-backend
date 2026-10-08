import Link from "next/link";

import { ButtonLink } from "@/components/button";
import { Label } from "@/components/label";
import { Logo, Symbol } from "@/components/logo";
import { hasSession } from "@/lib/api";

const STATIONS = [
  ["Idea", "Founder"],
  ["Product", "PM"],
  ["UX/UI", "Designer"],
  ["System", "Architect"],
  ["Build", "Engineer"],
  ["Test", "QA"],
  ["Deploy", "DevOps"],
  ["Run", "SRE"],
  ["Iterate", "You, again"],
];

const LOOP = [
  {
    title: "Build it your way",
    body: "Your editor, your GitHub, your hosting. Real tools from the first day, nothing sandboxed.",
  },
  {
    title: "We check the work",
    body: "Hit “Check my work” and we test what you shipped, then tell you exactly what we saw and how to fix it.",
  },
  {
    title: "It goes live",
    body: "Every path ends with a real URL people can use. Not a certificate. A product.",
  },
];

export default async function Landing() {
  const signedIn = await hasSession();

  return (
    <main id="main">
      <section className="relative overflow-hidden bg-carbon text-paper">
        <Symbol
          size={420}
          tone="ink"
          className="pointer-events-none absolute right-[-60px] top-36 hidden lg:block [&>path:first-child]:fill-carbon-3"
        />
        <nav className="relative mx-auto flex max-w-6xl items-center justify-between px-4 py-6 sm:px-6">
          <Logo tone="paper" />
          <div className="flex items-center gap-2 sm:gap-6">
            {signedIn ? (
              <ButtonLink href="/home" variant="inverse" className="py-2">
                Open dashboard
              </ButtonLink>
            ) : (
              <>
                <Link href="/login" className="px-2 text-sm text-carbon-muted hover:text-paper">
                  Sign in
                </Link>
                <ButtonLink href="/signup" variant="inverse" className="py-2">
                  Start building
                </ButtonLink>
              </>
            )}
          </div>
        </nav>

        <div className="relative mx-auto max-w-6xl px-4 pb-24 pt-14 sm:px-6 sm:pt-24">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-orange">
            Idea → production · 9 stations
          </p>
          <h1 className="mt-6 max-w-4xl font-display text-5xl font-extrabold leading-[0.95] tracking-[-0.04em] sm:text-7xl lg:text-8xl">
            Nobody&rsquo;s coming to build it. <span className="text-orange">Good.</span>
          </h1>
          <p className="mt-8 max-w-xl text-lg leading-relaxed text-carbon-muted">
            Learn every role a product team splits, by shipping real products. Start with an idea.
            Finish with a URL.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <ButtonLink href={signedIn ? "/home" : "/signup"} variant="inverse">
              Start your first build →
            </ButtonLink>
            <a href="#how" className="inline-flex min-h-11 items-center border-2 border-paper px-5 py-3 font-semibold hover:bg-paper hover:text-ink">
              How it works
            </a>
          </div>

          <ol className="mt-20 grid grid-cols-3 gap-px border border-carbon-line bg-carbon-line sm:grid-cols-9" aria-label="The nine stations">
            {STATIONS.map(([station, role], index) => (
              <li key={station} className="bg-carbon p-3">
                <span className={`block h-1.5 ${index < 6 ? "bg-patina" : index === 6 ? "bg-orange" : "bg-carbon-line"}`} />
                <p className="mt-3 font-mono text-[0.7rem] text-carbon-muted">{String(index + 1).padStart(2, "0")}</p>
                <p className="font-display text-sm font-bold">{station}</p>
                <p className="text-xs text-carbon-muted">{role}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section id="how" className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <Label>How it works</Label>
        <h2 className="mt-4 max-w-2xl font-display text-4xl font-bold tracking-[-0.03em] sm:text-5xl">
          Tutorials end. Products don&rsquo;t.
        </h2>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {LOOP.map((item, index) => (
            <div key={item.title} className={`border-2 border-ink bg-elevated p-7 ${index === 1 ? "shadow-hard-orange" : "shadow-hard"}`}>
              <p className="font-mono text-xs text-orange-dark">0{index + 1}</p>
              <h3 className="mt-3 font-display text-2xl font-bold">{item.title}</h3>
              <p className="mt-3 leading-relaxed text-body">{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-[linear-gradient(135deg,var(--color-orange)_0%,var(--color-orange)_55%,var(--color-brass)_100%)]">
        <div className="mx-auto flex max-w-6xl flex-col items-start gap-8 px-4 py-20 sm:px-6 md:flex-row md:items-end md:justify-between">
          <h2 className="font-display text-5xl font-extrabold leading-[0.95] tracking-[-0.04em] sm:text-7xl">
            Make it exist.
          </h2>
          <ButtonLink href={signedIn ? "/home" : "/signup"} variant="dark">
            Start building
          </ButtonLink>
        </div>
      </section>

      <footer className="mx-auto flex max-w-6xl items-center justify-between px-4 py-10 text-sm text-muted sm:px-6">
        <Logo size={20} />
        <p>Built for people who build things.</p>
      </footer>
    </main>
  );
}
