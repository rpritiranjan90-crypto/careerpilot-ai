import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E test configuration.
 *
 * Targets the full-stack dev environment (frontend on :3000, backend on :8000).
 * Set BASE_URL to override.
 *
 * Run:
 *   npm run e2e           – headless
 *   npm run e2e:ui        – browser UI
 *   npm run e2e:install   – install Chromium / deps
 */
const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,  // sequential to avoid DB/test-state conflicts
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: process.env.CI
    ? undefined  // In CI the services are already running; the docker-compose.yml
    :            // health-checks ensure they're up before tests start.
    {
      command: "docker compose -f ../docker-compose.yml up",
      url: "http://localhost:3000",
      reuseExistingServer: false,
      timeout: 120_000,
      cwd: "..",
    },
});
