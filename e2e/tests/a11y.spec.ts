import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { signIn } from "./helpers";

/** WCAG 2.2 AA: no serious or critical violations on any main screen. */
async function audit(page: Page, path: string) {
  await page.goto(path);
  await page.waitForLoadState("networkidle");
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
  const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect.soft(
    serious.map((v) => `${v.id}: ${v.help} (${v.nodes.map((n) => n.target.join(" ")).slice(0, 3).join(", ")})`),
    `${path} has accessibility violations`,
  ).toEqual([]);
}

test("public screens are accessible", async ({ page }) => {
  for (const path of ["/", "/login", "/signup", "/forgot-password", "/forgot-password?sent=1&email=a%40b.co", "/reset-password"]) {
    await audit(page, path);
  }
});

test("app screens are accessible", async ({ page }) => {
  await signIn(page, "grace@onefold.local", "onefold");
  for (const path of ["/home", "/path", "/steps/go-live", "/steps/problem-statement", "/project"]) {
    await audit(page, path);
  }
});

test("onboarding is accessible", async ({ page }) => {
  await signIn(page, "new@onefold.local", "onefold");
  for (const step of [1, 2, 3, 4]) await audit(page, `/onboarding?step=${step}`);
});
