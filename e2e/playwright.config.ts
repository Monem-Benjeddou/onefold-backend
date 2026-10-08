import { defineConfig, devices } from "@playwright/test";

/**
 * Runs against a stack that is already up (docker compose, or the CI job):
 *   WEB_URL      the web app        (default http://localhost:3000)
 *   MAILPIT_URL  the local inbox    (default http://localhost:8025)
 * CHROMIUM_PATH points at a preinstalled Chromium when browsers can't be downloaded.
 */
export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.WEB_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "phone", use: { ...devices["Pixel 7"] }, grep: /@phone/ },
  ],
});
