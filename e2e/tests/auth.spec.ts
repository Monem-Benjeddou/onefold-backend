import { expect, test } from "@playwright/test";

import { STRONG, alert, finishOnboarding, latestEmail, linkIn, signIn, signUp, uniqueEmail } from "./helpers";

test("sign up, confirm the email, and land in onboarding", async ({ page }) => {
  const email = uniqueEmail("signup");
  await signUp(page, email);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("What do you want to exist");

  const message = await latestEmail(email, "Confirm your email");
  await page.goto(linkIn(message.Text, "/verify-email"));
  await page.getByRole("button", { name: "Confirm my email" }).click();
  await expect(page.getByRole("heading", { name: "Email confirmed" })).toBeVisible();
});

test("sign-up explains field problems inline", async ({ page }) => {
  await page.goto("/signup");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("Enter your email address.")).toBeVisible();
  await expect(page.getByLabel("Email")).toBeFocused();

  await page.getByLabel("Email").fill("ada@onefold.local");
  await page.getByLabel("Password", { exact: true }).fill(STRONG);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("An account with this email already exists.")).toBeVisible();
  await expect(page.getByRole("link", { name: "Sign in instead" })).toBeVisible();
});

test("password sign-in, wrong password, and sign-out", async ({ page }) => {
  await signIn(page, "ada@onefold.local", "wrong password!", { expectSuccess: false });
  await expect(alert(page, "That email and password don't match.")).toBeVisible();
  await expect(page.getByLabel("Password", { exact: true })).toHaveValue("");

  await signIn(page, "ada@onefold.local", "onefold");
  await expect(page).toHaveURL(/\/home/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Ada");

  // Signed in: the login page sends you straight back.
  await page.goto("/login");
  await expect(page).toHaveURL(/\/home/);

  await page.getByRole("button", { name: "Account menu" }).first().click();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login\?signed_out=1/);
  await expect(page.getByText("You're signed out.")).toBeVisible();
});

test("demo accounts sign in with one click", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: /linus@onefold\.local/ }).click();
  await expect(page).toHaveURL(/\/home/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Linus");
});

test("forgot password, reset from the email, signed in", async ({ page, context }) => {
  const email = uniqueEmail("reset");
  await signUp(page, email);
  await context.clearCookies();

  await page.goto(`/login?email=${encodeURIComponent(email)}`);
  await page.getByRole("link", { name: "Forgot password?" }).click();
  await expect(page.getByLabel("Email")).toHaveValue(email);
  await page.getByRole("button", { name: "Send reset link" }).click();
  await expect(page.getByRole("heading", { name: "Reset link sent" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Open local inbox" })).toBeVisible();

  const message = await latestEmail(email, "Reset your Onefold password");
  await page.goto(linkIn(message.Text, "/reset-password"));
  await page.getByLabel("New password").fill(`${STRONG}!`);
  await page.getByLabel("Type it again").fill(`${STRONG}!`);
  await page.getByRole("button", { name: "Save password and sign in" }).click();
  await expect(page).toHaveURL(/\/onboarding/);

  // The link only works once.
  await page.goto(linkIn(message.Text, "/reset-password"));
  await page.getByLabel("New password").fill(`${STRONG}?`);
  await page.getByLabel("Type it again").fill(`${STRONG}?`);
  await page.getByRole("button", { name: "Save password and sign in" }).click();
  await expect(alert(page, "already used")).toBeVisible();
});

test("email sign-in link from the inbox", async ({ page }) => {
  const email = uniqueEmail("magic");
  await page.goto("/login");
  await page.getByRole("button", { name: /Email me a sign-in link instead/ }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  await expect(page.getByRole("heading", { name: "Check your inbox." })).toBeVisible();

  const message = await latestEmail(email, "sign-in link");
  await page.goto(linkIn(message.Text, "/auth/verify"));
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/onboarding/);
  await finishOnboarding(page);
});
