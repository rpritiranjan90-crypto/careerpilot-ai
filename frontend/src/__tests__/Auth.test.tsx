import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "../hooks/useAuth";
import { setAccessToken, getAccessToken } from "../services/api";
import * as supabaseModule from "../services/supabase";

describe("Auth System and useAuth Hook", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("initializes with null user when no token and no Supabase session exists", async () => {
    vi.spyOn(supabaseModule, "isSupabaseConfigured").mockReturnValue(false);
    vi.spyOn(supabaseModule, "getSupabase").mockReturnValue(null);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it("does NOT restore a user from a plain (non-JWT) token in localStorage", () => {
    vi.spyOn(supabaseModule, "isSupabaseConfigured").mockReturnValue(true);
    vi.spyOn(supabaseModule, "getSupabase").mockReturnValue({
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
        onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
        signOut: vi.fn(),
      },
    } as any);
    // A plain text string is NOT a valid JWT. The hook must refuse to
    // treat it as an authenticated user.
    setAccessToken("developer-alice");

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    expect(result.current.user).toBeNull();
  });

  it("restores user session from active Supabase session", async () => {
    const mockSession = {
      access_token: "mock.supabase.jwt.token",
      user: {
        id: "supabase-user-uuid-1234",
        email: "alice@example.com",
      },
    };

    const mockSupabase = {
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: mockSession }, error: null }),
        onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
        signInWithPassword: vi.fn(),
        signUp: vi.fn(),
        signOut: vi.fn().mockResolvedValue({ error: null }),
      },
    };

    vi.spyOn(supabaseModule, "isSupabaseConfigured").mockReturnValue(true);
    vi.spyOn(supabaseModule, "getSupabase").mockReturnValue(mockSupabase as any);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await act(async () => {
      // Allow async initSession to complete
    });

    expect(result.current.user).toEqual({
      userId: "supabase-user-uuid-1234",
      email: "alice@example.com",
    });
    expect(getAccessToken()).toBe("mock.supabase.jwt.token");
  });

  it("authenticates via Supabase signInWithPassword on valid credentials", async () => {
    const mockSession = {
      access_token: "real.supabase.jwt.token",
      user: {
        id: "user-uuid-real-5678",
        email: "bob@example.com",
      },
    };

    const mockSupabase = {
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
        onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
        signInWithPassword: vi.fn().mockResolvedValue({ data: { session: mockSession }, error: null }),
        signUp: vi.fn(),
        signOut: vi.fn(),
      },
    };

    vi.spyOn(supabaseModule, "isSupabaseConfigured").mockReturnValue(true);
    vi.spyOn(supabaseModule, "getSupabase").mockReturnValue(mockSupabase as any);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    let res: any;
    await act(async () => {
      res = await result.current.signInWithEmail("bob@example.com", "SecretPass123!");
    });

    expect(res.ok).toBe(true);
    expect(mockSupabase.auth.signInWithPassword).toHaveBeenCalledWith({
      email: "bob@example.com",
      password: "SecretPass123!",
    });
    expect(result.current.user?.userId).toBe("user-uuid-real-5678");
    expect(getAccessToken()).toBe("real.supabase.jwt.token");
  });

  it("rejects invalid Supabase credentials with friendly error message", async () => {
    const mockSupabase = {
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
        onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
        signInWithPassword: vi.fn().mockResolvedValue({
          data: { session: null },
          error: { message: "Invalid login credentials" },
        }),
        signUp: vi.fn(),
        signOut: vi.fn(),
      },
    };

    vi.spyOn(supabaseModule, "isSupabaseConfigured").mockReturnValue(true);
    vi.spyOn(supabaseModule, "getSupabase").mockReturnValue(mockSupabase as any);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    let res: any;
    await act(async () => {
      res = await result.current.signInWithEmail("bob@example.com", "WrongPassword");
    });

    expect(res.ok).toBe(false);
    expect(res.error).toBe("Invalid email or password.");
    expect(result.current.user).toBeNull();
  });

  it("registers new account via Supabase signUp", async () => {
    const mockSupabase = {
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
        onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
        signInWithPassword: vi.fn(),
        signUp: vi.fn().mockResolvedValue({
          data: {
            user: { id: "new-user-123", email: "new@example.com" },
            session: null,
          },
          error: null,
        }),
        signOut: vi.fn(),
      },
    };

    vi.spyOn(supabaseModule, "isSupabaseConfigured").mockReturnValue(true);
    vi.spyOn(supabaseModule, "getSupabase").mockReturnValue(mockSupabase as any);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    let res: any;
    await act(async () => {
      res = await result.current.signUpWithEmail("new@example.com", "StrongPassword123!");
    });

    expect(res.ok).toBe(true);
    expect(res.message).toContain("confirm your account");
    expect(mockSupabase.auth.signUp).toHaveBeenCalledWith({
      email: "new@example.com",
      password: "StrongPassword123!",
    });
  });

  it("signs out and clears tokens via Supabase signOut", async () => {
    const mockSupabase = {
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
        onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
        signInWithPassword: vi.fn(),
        signUp: vi.fn(),
        signOut: vi.fn().mockResolvedValue({ error: null }),
      },
    };

    vi.spyOn(supabaseModule, "isSupabaseConfigured").mockReturnValue(true);
    vi.spyOn(supabaseModule, "getSupabase").mockReturnValue(mockSupabase as any);

    setAccessToken("active-token");

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await act(async () => {
      await result.current.signOut();
    });

    expect(mockSupabase.auth.signOut).toHaveBeenCalled();
    expect(getAccessToken()).toBeNull();
    expect(result.current.user).toBeNull();
  });
});
