import { CheckIcon } from "@/components/icons";

export function passwordRules(password: string, email = "", min = 10) {
  const local = email.split("@")[0]?.toLowerCase() ?? "";
  return [
    { label: `At least ${min} characters`, met: password.length >= min },
    { label: "Not only numbers", met: password.length > 0 && !/^\d+$/.test(password) },
    {
      label: "Doesn't contain your email",
      met: password.length > 0 && !(local.length >= 3 && password.toLowerCase().includes(local)),
    },
  ];
}

/** 0–4. A guide, not a gate: the API makes the final call (including common-password checks). */
export function passwordScore(password: string, email = "", min = 10) {
  if (!passwordRules(password, email, min).every((rule) => rule.met)) return password ? 1 : 0;
  const classes = [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((re) => re.test(password)).length;
  let score = 1;
  if (password.length >= 12) score++;
  if (password.length >= 16) score++;
  if (classes >= 3) score++;
  return Math.min(4, score);
}

const LABELS = ["", "Too weak", "Okay", "Strong", "Very strong"];
const COLORS = ["bg-line", "bg-error", "bg-brass", "bg-patina", "bg-patina"];

export function PasswordStrength({ password, email, min = 10 }: { password: string; email?: string; min?: number }) {
  const score = passwordScore(password, email, min);
  const rules = passwordRules(password, email, min);
  return (
    <div className="mt-3" aria-live="polite">
      <div className="flex gap-1" aria-hidden="true">
        {[1, 2, 3, 4].map((step) => (
          <span key={step} className={`h-1.5 flex-1 ${score >= step ? COLORS[score] : "bg-line"}`} />
        ))}
      </div>
      {password && <p className="mt-1.5 font-mono text-xs text-muted">Strength: {LABELS[score]}</p>}
      <ul className="mt-2 space-y-1">
        {rules.map((rule) => (
          <li key={rule.label} className={`flex items-center gap-2 text-sm ${rule.met ? "text-success" : "text-muted"}`}>
            <span className={`flex h-4 w-4 items-center justify-center border ${rule.met ? "border-success bg-success text-paper" : "border-line"}`}>
              {rule.met && <CheckIcon size={11} strokeWidth={3.5} />}
            </span>
            {rule.label}
            <span className="sr-only">{rule.met ? "(done)" : "(not yet)"}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
