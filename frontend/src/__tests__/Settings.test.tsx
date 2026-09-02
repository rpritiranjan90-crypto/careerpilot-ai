import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SettingsPage } from "../pages/SettingsPage";
import { AuthProvider } from "../hooks/useAuth";
import * as api from "../services/api";
import * as supabaseModule from "../services/supabase";

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return {
    ...actual,
    deleteAccount: vi.fn(),
  };
});

/** Build a mock Supabase client that returns a specific session. */
function makeMockSupabase(userId: string, email: string) {
  return {
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: {
          session: {
            access_token: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${btoa(JSON.stringify({ sub: userId, email }))}.sig`,
            user: { id: userId, email },
          },
        },
        error: null,
      }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } },
      }),
      signOut: vi.fn().mockResolvedValue({ error: null }),
    },
  };
}

describe("SettingsPage Component & GDPR Article 17 Erasure", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("renders user profile info and GDPR erasure section", async () => {
    vi.spyOn(supabaseModule, "isSupabaseConfigured").mockReturnValue(true);
    vi.spyOn(supabaseModule, "getSupabase").mockReturnValue(
      makeMockSupabase("test-user-settings", "test@example.com") as any
    );

    render(
      <AuthProvider>
        <SettingsPage />
      </AuthProvider>
    );

    // Wait for the async session init
    await act(async () => {});

    expect(screen.getByRole("heading", { name: /settings/i })).toBeInTheDocument();
    expect(screen.getByText("test-user-settings")).toBeInTheDocument();
    expect(screen.getByText(/data & privacy \(gdpr article 17\)/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /delete my account & all personal data/i })
    ).toBeInTheDocument();
  });

  it("toggles delete confirmation modal and cancels safely", async () => {
    vi.spyOn(supabaseModule, "isSupabaseConfigured").mockReturnValue(true);
    vi.spyOn(supabaseModule, "getSupabase").mockReturnValue(
      makeMockSupabase("test-user-settings", "test@example.com") as any
    );

    render(
      <AuthProvider>
        <SettingsPage />
      </AuthProvider>
    );
    await act(async () => {});

    const user = userEvent.setup();

    await user.click(
      screen.getByRole("button", { name: /delete my account & all personal data/i })
    );

    expect(
      screen.getByText(/are you sure\? this action is permanent and cannot be undone/i)
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /cancel/i }));

    expect(
      screen.queryByText(/are you sure\? this action is permanent and irreversible/i)
    ).not.toBeInTheDocument();
    expect(api.deleteAccount).not.toHaveBeenCalled();
  });

  it("executes GDPR account erasure and displays confirmation message", async () => {
    vi.spyOn(supabaseModule, "isSupabaseConfigured").mockReturnValue(true);
    vi.spyOn(supabaseModule, "getSupabase").mockReturnValue(
      makeMockSupabase("test-user-to-delete", "delete@example.com") as any
    );

    vi.mocked(api.deleteAccount).mockResolvedValue({
      data: {
        message: "Account and associated data deleted successfully.",
        deleted_user_id: "test-user-to-delete",
      },
      status: 200,
    });

    render(
      <AuthProvider>
        <SettingsPage />
      </AuthProvider>
    );
    await act(async () => {});

    const user = userEvent.setup();

    await user.click(
      screen.getByRole("button", { name: /delete my account & all personal data/i })
    );
    await user.click(screen.getByRole("button", { name: /yes, permanently delete everything/i }));

    await waitFor(() => {
      expect(api.deleteAccount).toHaveBeenCalled();
      expect(
        screen.getByText(/your account and all associated data have been permanently erased/i)
      ).toBeInTheDocument();
    });
  });
});
