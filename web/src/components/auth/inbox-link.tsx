import { MailIcon } from "@/components/icons";
import { buttonClass } from "@/components/button";

/** Development only: the local inbox (Mailpit), so nobody has to read logs for a link. */
export function InboxLink({ url }: { url: string }) {
  if (!url) return null;
  return (
    <div className="mt-6 border-2 border-dashed border-ink/40 bg-surface p-4">
      <p className="font-mono text-[0.68rem] uppercase tracking-[0.12em] text-muted">Development</p>
      <p className="mt-1 text-sm text-body">Emails don&rsquo;t leave your machine. They land in the local inbox.</p>
      <a href={url} target="_blank" rel="noreferrer" className={buttonClass("dark", "mt-3 w-full")}>
        <MailIcon /> Open local inbox
      </a>
    </div>
  );
}
