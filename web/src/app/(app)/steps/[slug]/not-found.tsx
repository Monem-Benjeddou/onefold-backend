import { ButtonLink } from "@/components/button";
import { Label } from "@/components/label";

export default function StepNotFound() {
  return (
    <div className="mx-auto max-w-2xl py-10">
      <Label>Not on your path</Label>
      <h1 className="mt-3 font-display text-4xl font-bold tracking-[-0.03em]">That step doesn&rsquo;t exist.</h1>
      <p className="mt-4 text-lg text-body">The link may be old, or the step was renamed in a newer version of the path.</p>
      <div className="mt-8 flex flex-wrap gap-4">
        <ButtonLink href="/home">Go to your next step</ButtonLink>
        <ButtonLink href="/path" variant="secondary">
          See the whole path
        </ButtonLink>
      </div>
    </div>
  );
}
