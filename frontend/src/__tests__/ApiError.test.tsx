import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  getUserDashboard,
  getAccessToken,
  setAccessToken,
  deleteAccount,
  listResumes,
} from "../services/api";

describe("API Client Error Handling and Envelopes", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("extracts error message from structured JSON envelope { error: { message: '...' } }", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({
        error: {
          code: "VALIDATION_ERROR",
          message: "Uploaded file format is invalid.",
        },
      }),
    } as Response);

    const res = await listResumes();
    expect(res.status).toBe(400);
    expect(res.error).toBe("Uploaded file format is invalid.");
  });

  it("extracts detail message from standard FastAPI { detail: '...' } error response", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({
        detail: "Access denied to this resource.",
      }),
    } as Response);

    const res = await listResumes();
    expect(res.status).toBe(403);
    expect(res.error).toBe("Access denied to this resource.");
  });

  it("handles 401 Unauthorized by clearing access token and dispatching auth:logout", async () => {
    setAccessToken("active-expired-token");
    const logoutListener = vi.fn();
    window.addEventListener("auth:logout", logoutListener);

    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({
        error: { message: "Token has expired" },
      }),
    } as Response);

    const res = await getUserDashboard();
    expect(res.status).toBe(401);
    expect(getAccessToken()).toBeNull();
    expect(logoutListener).toHaveBeenCalledTimes(1);

    window.removeEventListener("auth:logout", logoutListener);
  });

  it("handles 204 No Content response gracefully with undefined data and 204 status", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      status: 204,
      json: async () => null,
    } as unknown as Response);

    const res = await deleteAccount();
    expect(res.status).toBe(204);
    expect(res.data).toBeUndefined();
    expect(res.error).toBeUndefined();
  });

  it("handles network failure and returns user-friendly connection error", async () => {
    vi.spyOn(global, "fetch").mockRejectedValueOnce(
      new TypeError("Failed to fetch")
    );

    const res = await getUserDashboard();
    expect(res.error).toBe("Unable to connect to the server.");
  });
});
