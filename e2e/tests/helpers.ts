import { expect, type Page } from "@playwright/test";

export const MAILPIT = process.env.MAILPIT_URL ?? "http://localhost:8025";
export const STRONG = "correct horse battery";

export function uniqueEmail(tag: string) {
  return `e2e-${tag}-${Date.now()}-${Math.floor(Math.random() * 1e4)}@example.com`;
}

/** The newest email to `to`, waiting for it to arrive in Mailpit. */
export async function latestEmail(to: string, subject?: string) {
  for (let attempt = 0; attempt < 30; attempt++) {
    const search = await fetch(`${MAILPIT}/api/v1/search?query=${encodeURIComponent(`to:"${to}"`)}`);
    const { messages = [] } = (await search.json()) as { messages?: { ID: string; Subject: string }[] };
    const match = messages.find((m) => !subject || m.Subject.includes(subject));
    if (match) {
      const message = (await (await fetch(`${MAILPIT}/api/v1/message/${match.ID}`)).json()) as { Text: string; Subject: string };
      return message;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`No email to ${to}${subject ? ` about "${subject}"` : ""}`);
}

export function linkIn(text: string, path: string) {
  const match = text.match(new RegExp(`https?://[^\\s]+${path.replace("/", "\\/")}\\?token=[\\w-]+`));
  if (!match) throw new Error(`No ${path} link in email`);
  return new URL(match[0]).pathname + new URL(match[0]).search;
}

export async function signUp(page: Page, email: string, name = "Eve Builder") {
  await page.goto("/signup");
  await page.getByLabel("Your name").fill(name);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(STRONG);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/\/onboarding/);
}

export async function signIn(page: Page, email: string, password = STRONG, { expectSuccess = true } = {}) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  if (expectSuccess) await expect(page).toHaveURL(/\/(home|onboarding|project|path)/);
}

/** Our alerts (Next.js also renders an empty role="alert" route announcer). */
export function alert(page: Page, text: string | RegExp) {
  return page.getByRole("alert").filter({ hasText: text });
}

export async function finishOnboarding(page: Page) {
  await page.getByRole("button", { name: /Continue|Skip for now/ }).click();
  await page.getByRole("button", { name: /Continue/ }).click(); // pace has a default
  await page.getByText("Deployed once or twice").click();
  await page.getByRole("button", { name: /Continue/ }).click();
  await page.getByText("Habit Loop").click();
  await page.getByRole("button", { name: /Start building/ }).click();
  await expect(page).toHaveURL(/\/home/);
}
