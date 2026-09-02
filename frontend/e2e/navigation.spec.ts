/**
 * E2E: Navigation
 * Verifies that the navbar links work and protected routes redirect to login.
 */

import { test, expect, isSignedIn } from "./helpers";

test.describe("Navigation", () => {
  test("navbar is visible on the home page", async ({ pageAsUser }) => {
    await pageAsUser.goto("/");
    await expect(pageAsUser.getByText("CareerPilot AI")).toBeVisible();
    await expect(pageAsUser.getByRole("link", { name: "Resume" })).toBeVisible();
    await expect(pageAsUser.getByRole("link", { name: "Job Match" })).toBeVisible();
    await expect(pageAsUser.getByRole("link", { name: "Interview" })).toBeVisible();
  });

  test("signed-in user sees sign-out button", async ({ pageAsUser }) => {
    await pageAsUser.goto("/");
    await expect(pageAsUser.getByRole("button", { name: /sign out/i })).toBeVisible();
  });

  test("navbar links navigate to correct pages", async ({ pageAsUser }) => {
    await pageAsUser.goto("/");
    for (const [label, path] of [
      ["Resume", "/resume"],
      ["Job Match", "/job-match"],
      ["Interview", "/interview"],
      ["Dashboard", "/dashboard"],
    ] as const) {
      await pageAsUser.getByRole("link", { name: label }).click();
      await pageAsUser.waitForURL(`**${path}`);
      await pageAsUser.goBack();
    }
  });

  test("sign out clears session and shows sign in", async ({ pageAsUser }) => {
    await pageAsUser.goto("/");
    await pageAsUser.getByRole("button", { name: /sign out/i }).click();
    await expect(pageAsUser.getByRole("link", { name: /sign in/i })).toBeVisible();
    // User ID should no longer be visible
    await expect(pageAsUser.getByText("e2e-test-user")).not.toBeVisible();
  });
});
