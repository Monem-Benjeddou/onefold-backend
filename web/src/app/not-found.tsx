import { ButtonLink } from "@/components/button";
import { Logo } from "@/components/logo";

export default function NotFound() {
  return (
    <main id="main" className="flex min-h-dvh flex-col items-start justify-center gap-6 bg-carbon px-6 text-paper sm:px-16">
      <Logo tone="paper" />
      <h1 className="font-display text-6xl font-extrabold tracking-[-0.04em]">404.</h1>
      <p className="text-lg text-carbon-muted">This page shipped nowhere.</p>
      <ButtonLink href="/" variant="inverse">
        Go home
      </ButtonLink>
    </main>
  );
}
