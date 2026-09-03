/**
 * E2E: Authentication flow
 * Verifies login page renders, dev-mode sign-in works, and
 * unauthenticated users are redirected to /login.
 */

import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test("login page renders correctly", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
    await expect(page.getByPlaceholder(/user id/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  });

  test("signing in with dev mode redirects to home", async ({ page }) => {
    await page.goto("/login");
    await page.getByPlaceholder(/user id/i).fill("dev-user-123");
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL("/");
    await expect(page.getByText("dev-user-123")).toBeVisible();
  });

  test("protected route redirects to login", async ({ page }) => {
    await page.goto("/resume");
    // Should redirect to /login
    await page.waitForURL(/\/login/);
    await expect(page.getByPlaceholder(/user id/i)).toBeVisible();
  });

  test("protected route redirects to login on direct navigation", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForURL(/\/login/);
  });

  test("session persists across page reloads", async ({ page }) => {
    // Sign in
    await page.goto("/login");
    await page.getByPlaceholder(/user id/i).fill("session-test");
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL("/");

    // Reload – should still be signed in
    await page.reload();
    await expect(page.getByText("session-test")).toBeVisible();
  });

  test("sign out clears session on reload", async ({ page }) => {
    // Sign in
    await page.goto("/login");
    await page.getByPlaceholder(/user id/i).fill("signout-test");
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL("/");

    // Sign out
    await page.getByRole("button", { name: /sign out/i }).click();

    // Reload – should be signed out
    await page.reload();
    await expect(page.getByRole("link", { name: /sign in/i })).toBeVisible();
    await expect(page.getByText("signout-test")).not.toBeVisible();
  });
});
