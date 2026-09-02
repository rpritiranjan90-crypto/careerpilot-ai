/**
 * E2E helpers: authentication and navigation utilities used across test files.
 */

import { test as base, Page } from "@playwright/test";

/**
 * Signed-in test fixture: navigates to /login, enters a dev user ID,
 * and signs in.  This works because dev mode accepts any user_id.
 */
export const test = base.extend<{ pageAsUser: Page }>({
  pageAsUser: async ({ page }, use) => {
    await page.goto("/login");
    // Enter a dev-mode user ID
    const input = page.getByPlaceholder(/user id/i);
    await input.fill("e2e-test-user");
    await page.getByRole("button", { name: /sign in/i }).click();
    // Wait for the redirect to complete
    await page.waitForURL("/");
    await use(page);
  },
});

export { expect } from "@playwright/test";

/** Returns true if the current page shows the user as signed in. */
export function isSignedIn(page: Page): Promise<boolean> {
  return page.getByText("e2e-test-user").isVisible();
}
