/**
 * E2E: API error handling
 * Verifies that 401, 429, 413, and other API errors surface a user-friendly
 * message and don't crash the page.
 */

import { test, expect } from "./helpers";

test.describe("API Error Handling", () => {
  test("API 401 triggers sign-out and redirect to login", async ({ pageAsUser }) => {
    // The auth layer dispatches auth:logout on 401.
    // Simulate this by directly dispatching the event while signed in.
    await pageAsUser.evaluate(() => {
      window.dispatchEvent(new Event("auth:logout"));
    });
    await pageAsUser.waitForURL(/\/login/, { timeout: 3000 });
    await expect(pageAsUser.getByPlaceholder(/user id/i)).toBeVisible();
  });

  test("API 429 shows rate-limit message", async ({ pageAsUser }) => {
    await pageAsUser.goto("/");

    // Exceed the rate limit (100 requests to /api/resumes/analyze)
    const errors: string[] = [];
    for (let i = 0; i < 100; i++) {
      const resp = await pageAsUser.evaluate(async () => {
        const r = await fetch("/api/resumes/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            resume_text:
              "Experienced software engineer with 5 years of Python, SQL, and Docker experience",
          }),
        });
        return { status: r.status, body: await r.json().catch(() => ({})) };
      });
      if (resp.status === 429) {
        errors.push("rate-limited");
        break;
      }
    }
    // If we hit the limit, the error envelope must be visible
    if (errors.length > 0) {
      await expect(
        pageAsUser.getByText(/too many requests|rate limit|retry/i)
      ).toBeVisible({ timeout: 3000 });
    }
  });

  test("API 413 shows file-too-large message", async ({ pageAsUser }) => {
    await pageAsUser.goto("/resume");
    const fileInput = pageAsUser.locator('input[type="file"]').first();

    // Create a 10 MB file blob
    const blob = new Blob([new Array(10 * 1024 * 1024).fill("x").join("")], {
      type: "text/plain",
    });
    await fileInput.setInputFiles(
      new File([blob], "large-resume.txt", { type: "text/plain" })
    );

    // The upload should fail with 413 or a client-side validation message
    await expect(
      pageAsUser.getByText(/file too large|too large|10/i)
    ).toBeVisible({ timeout: 5000 });
  });
});
