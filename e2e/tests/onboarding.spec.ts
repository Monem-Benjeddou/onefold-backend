import { expect, test } from "@playwright/test";

import { signUp, uniqueEmail } from "./helpers";

test("onboarding survives a refresh and finishes in one go", async ({ page }) => {
  await signUp(page, uniqueEmail("onboarding"), "Grace Hopper");

  await page.getByLabel(/Your idea/).fill("Help freelancers chase late invoices without being awkward.");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL(/step=2/);
  await page.getByText("10+ hours a week").click();
  await expect(page.getByText("✓ Saved")).toBeVisible();

  // Refresh mid-way: same step, same answers.
  await page.reload();
  await expect(page).toHaveURL(/step=2/);
  await expect(page.getByRole("radio", { name: /10\+ hours a week/ })).toBeChecked();

  // Back goes to the idea, still filled in.
  await page.getByRole("button", { name: "Back" }).click();
  await expect(page.getByLabel(/Your idea/)).toHaveValue(/late invoices/);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();

  // Experience is required.
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByText("Pick the one closest to you.")).toBeVisible();
  await page.getByText("Never deployed anything").click();
  await page.getByRole("button", { name: "Continue" }).click();

  // Own idea: pre-filled from step 1; name required.
  await page.getByText("My own idea").click();
  await expect(page.getByLabel("The idea in one sentence")).toHaveValue(/late invoices/);
  await page.getByRole("button", { name: /Start building/ }).click();
  await expect(page.getByText("Give it a working name.")).toBeVisible();
  await page.getByLabel("Working name").fill("Invoice Nudge");
  await page.getByRole("button", { name: /Start building/ }).click();

  await expect(page).toHaveURL(/\/home\?welcome=1/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Let's build, Grace.");
  await expect(page.getByText("How this works")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Invoice Nudge" })).toBeVisible();

  // Done means done: onboarding sends you home now.
  await page.goto("/onboarding");
  await expect(page).toHaveURL(/\/home/);
});

test("signed-out visitors are sent to sign in and back", async ({ page }) => {
  await page.goto("/project");
  await expect(page).toHaveURL(/\/login\?next=%2Fproject/);
  await page.getByLabel("Email").fill("grace@onefold.local");
  await page.getByLabel("Password", { exact: true }).fill("onefold");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/project$/);
});
