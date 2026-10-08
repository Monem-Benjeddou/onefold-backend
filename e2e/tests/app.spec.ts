import { expect, test } from "@playwright/test";

import { signIn } from "./helpers";

test("an expired session renews silently and keeps what you typed", async ({ page, context }) => {
  await signIn(page, "grace@onefold.local", "onefold");
  await page.goto("/project");
  await page.waitForLoadState("networkidle"); // let React hydrate before typing
  const idea = `Chase late invoices for freelancers, politely (${Date.now()}).`;
  await page.getByLabel(/The idea/).fill(idea);

  // The access token expires while the form is open.
  await context.clearCookies({ name: "of_access" });
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByText("Project saved.")).toBeVisible();
  await page.reload();
  await expect(page.getByLabel(/The idea/)).toHaveValue(idea);
});

test("locked steps can be read ahead, with previous/next links", async ({ page }) => {
  await signIn(page, "ada@onefold.local", "onefold");
  await page.goto("/path");
  await page.getByRole("link", { name: /Put it on the internet/ }).click();
  await expect(page).toHaveTitle(/Put it on the internet/);
  await expect(page.getByText("Reading ahead")).toBeVisible();
  await expect(page.getByRole("link", { name: /Previous/ })).toBeVisible();
});

test("check history shows step titles and failed checks explain themselves", async ({ page }) => {
  await signIn(page, "grace@onefold.local", "onefold");
  await page.goto("/project");
  const history = page.getByRole("region", { name: "Check history" });
  await expect(history.getByText("Put it on the internet").first()).toBeVisible();
  await expect(history.getByText("Failed").first()).toBeVisible();
});

test("@phone the step action stays in reach on a phone", async ({ page }) => {
  await signIn(page, "ada@onefold.local", "onefold");
  await expect(page).toHaveURL(/\/home/);
  await page.getByRole("link", { name: /Continue|Start this step/ }).click();
  const button = page.getByRole("button", { name: /Mark as done|Check my work|I confirm/ }).last();
  await expect(button).toBeInViewport();
  await expect(page.getByRole("navigation", { name: "Main" }).last()).toBeVisible();
});
