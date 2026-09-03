/**
 * CareerPilot AI - Authentication Hook & Provider
 *
 * Implements production-grade Supabase email/password authentication with
 * automatic session restoration and token lifecycle management.
 *
 * Security invariants:
 *  - Password is never sent anywhere except supabase.auth.signInWithPassword
 *    / supabase.auth.signUp. The password is NEVER used as a token.
 *  - The access token stored in localStorage is always a real Supabase JWT.
 *    Plain text strings (including the email) cannot be used as identity.
 *  - The `userId` is always derived from the JWT's `sub` claim.
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { getAccessToken, setAccessToken } from "../services/api";
import { getSupabase, isSupabaseConfigured } from "../services/supabase";

export interface AuthUser {
  userId: string;
  email?: string;
}

export interface AuthResponse {
  ok: boolean;
  error?: string;
  message?: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  isSupabaseAuth: boolean;
  signInWithEmail: (email: string, password: string) => Promise<AuthResponse>;
  signUpWithEmail: (email: string, password: string) => Promise<AuthResponse>;
  signInWithOAuth: (provider: "google" | "github") => Promise<AuthResponse>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function parseJwtUser(token: string): AuthUser | null {
  const trimmed = token.trim();
  if (trimmed.startsWith("ey") && trimmed.includes(".")) {
    try {
      const payloadBase64 = trimmed.split(".")[1];
      const normalizedBase64 = payloadBase64.replace(/-/g, "+").replace(/_/g, "/");
      const decodedJson = JSON.parse(window.atob(normalizedBase64));
      const userId = decodedJson.sub || decodedJson.user_id;
      if (userId) {
        return {
          userId,
          email: decodedJson.email || undefined,
        };
      }
    } catch {
      // Invalid JWT format
    }
  }
  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const isSupabase = isSupabaseConfigured();
  const supabase = getSupabase();

  const [user, setUser] = useState<AuthUser | null>(() => {
    if (typeof window === "undefined") return null;
    const token = getAccessToken();
    if (!token) return null;
    // Only accept real Supabase JWTs. Plain text "dev tokens" are not
    // valid identities — they are not produced by any authentication flow.
    return parseJwtUser(token);
  });
  const [loading, setLoading] = useState(isSupabase);

  // Initialize and restore session
  useEffect(() => {
    let isMounted = true;

    async function initSession() {
      if (isSupabase && supabase) {
        try {
          const { data, error } = await supabase.auth.getSession();
          if (!error && data?.session) {
            setAccessToken(data.session.access_token);
            if (isMounted) {
              setUser({
                userId: data.session.user.id,
                email: data.session.user.email || undefined,
              });
            }
          } else {
            // No active Supabase session
            setAccessToken(null);
            if (isMounted) setUser(null);
          }
        } catch {
          if (isMounted) setUser(null);
        }
      }
      if (isMounted) setLoading(false);
    }

    initSession();

    // Listen to Supabase auth state changes
    let subscription: { unsubscribe: () => void } | null = null;
    if (isSupabase && supabase) {
      const { data } = supabase.auth.onAuthStateChange((_event, session) => {
        if (!isMounted) return;
        if (session) {
          setAccessToken(session.access_token);
          setUser({
            userId: session.user.id,
            email: session.user.email || undefined,
          });
        } else {
          setAccessToken(null);
          setUser(null);
        }
      });
      subscription = data.subscription;
    }

    return () => {
      isMounted = false;
      subscription?.unsubscribe();
    };
  }, [isSupabase, supabase]);

  // Listen for 401-style events from API client
  useEffect(() => {
    const handleLogoutEvent = async () => {
      if (isSupabase && supabase) {
        try {
          await supabase.auth.signOut();
        } catch {
          // Ignore
        }
      }
      setAccessToken(null);
      setUser(null);
    };

    window.addEventListener("auth:logout", handleLogoutEvent);
    return () => window.removeEventListener("auth:logout", handleLogoutEvent);
  }, [isSupabase, supabase]);

  const signInWithEmail = async (
    email: string,
    password: string
  ): Promise<AuthResponse> => {
    const cleanEmail = email ? email.trim() : "";
    if (!cleanEmail || !cleanEmail.includes("@")) {
      return { ok: false, error: "Please enter a valid email address." };
    }

    if (!password) {
      return { ok: false, error: "Please enter your password." };
    }

    // Production / Configured Supabase Flow
    if (isSupabase && supabase) {
      try {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: cleanEmail,
          password,
        });

        if (error) {
          let userMsg = "Invalid email or password.";
          if (error.message.toLowerCase().includes("email not confirmed")) {
            userMsg = "Please confirm your email address before signing in.";
          } else if (error.message.toLowerCase().includes("network") || error.message.toLowerCase().includes("fetch")) {
            userMsg = "Unable to reach authentication service. Please try again.";
          }
          return { ok: false, error: userMsg };
        }

        if (data?.session) {
          setAccessToken(data.session.access_token);
          setUser({
            userId: data.session.user.id,
            email: data.session.user.email || cleanEmail,
          });
          return { ok: true };
        }

        return { ok: false, error: "Sign-in did not return a valid session." };
      } catch {
        return {
          ok: false,
          error: "Unable to reach authentication service. Please try again.",
        };
      }
    }

    // Supabase is not configured — refuse to authenticate.
    // The frontend will NOT pretend to authenticate by treating the email as
    // a token. Local dev must run with a configured Supabase project.
    return {
      ok: false,
      error: "Authentication service is not configured. Please contact the administrator.",
    };
  };

  const signUpWithEmail = async (
    email: string,
    password: string
  ): Promise<AuthResponse> => {
    const cleanEmail = email ? email.trim() : "";
    if (!cleanEmail || !cleanEmail.includes("@")) {
      return { ok: false, error: "Please enter a valid email address." };
    }

    if (!password || password.length < 6) {
      return {
        ok: false,
        error: "Password must be at least 6 characters long.",
      };
    }

    if (!isSupabase || !supabase) {
      return {
        ok: false,
        error: "Account registration requires a configured Supabase project.",
      };
    }

    try {
      const { data, error } = await supabase.auth.signUp({
        email: cleanEmail,
        password,
      });

      if (error) {
        let userMsg = error.message;
        if (error.message.toLowerCase().includes("already registered")) {
          userMsg = "An account with this email address already exists.";
        }
        return { ok: false, error: userMsg };
      }

      if (data?.session) {
        setAccessToken(data.session.access_token);
        setUser({
          userId: data.session.user.id,
          email: data.session.user.email || cleanEmail,
        });
        return { ok: true };
      }

      if (data?.user) {
        return {
          ok: true,
          message: "Registration successful! Please check your email to confirm your account.",
        };
      }

      return { ok: false, error: "Registration failed. Please try again." };
    } catch {
      return {
        ok: false,
        error: "Unable to reach authentication service. Please try again.",
      };
    }
  };

  const signInWithOAuth = async (
    provider: "google" | "github"
  ): Promise<AuthResponse> => {
    if (!isSupabase || !supabase) {
      return {
        ok: false,
        error: "Social sign-in requires a configured Supabase project.",
      };
    }
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: typeof window !== "undefined" ? `${window.location.origin}/resume` : undefined,
        },
      });
      if (error) {
        return { ok: false, error: error.message };
      }
      return { ok: true };
    } catch {
      return {
        ok: false,
        error: "Unable to initiate social login. Please try again.",
      };
    }
  };

  const signOut = async () => {
    if (isSupabase && supabase) {
      try {
        await supabase.auth.signOut();
      } catch {
        // Ignore network errors on signout
      }
    }
    setAccessToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isSupabaseAuth: isSupabase,
        signInWithEmail,
        signUpWithEmail,
        signInWithOAuth,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    return {
      user: null,
      loading: false,
      isSupabaseAuth: false,
      signInWithEmail: async () => ({ ok: false, error: "Auth not initialized" }),
      signUpWithEmail: async () => ({ ok: false, error: "Auth not initialized" }),
      signInWithOAuth: async () => ({ ok: false, error: "Auth not initialized" }),
      signOut: async () => {},
    };
  }
  return ctx;
}
