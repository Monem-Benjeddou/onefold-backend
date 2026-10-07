/** Only same-site paths are allowed as redirect targets (no open redirects). */
export function safeNext(value: string | null | undefined, fallback = "/home"): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) {
    return fallback;
  }
  return value;
}

