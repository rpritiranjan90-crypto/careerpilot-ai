/**
 * CareerPilot AI - Supabase Client Configuration
 *
 * Centralized Supabase client initialization using public Vite environment variables.
 * Note: Never expose SUPABASE_JWT_SECRET to the frontend.
 *
 * Production auth: Supabase email/password via this client.
 * Development: DEV_TOKEN_AUTH=true on backend (bypasses Supabase; not production).
 */

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL ?? "";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY ?? "";

export function isSupabaseConfigured(): boolean {
  if (!supabaseUrl || !supabaseAnonKey) return false;
  const url = supabaseUrl.trim();
  const key = supabaseAnonKey.trim();
  if (
    url === "" ||
    key === "" ||
    url.includes("your-project.supabase.co") ||
    key === "your-anon-key" ||
    key === "your-anon-key-here"
  ) {
    return false;
  }
  return true;
}

/** Singleton Supabase client. Never null when isSupabaseConfigured() is true. */
let _supabase: SupabaseClient | null = null;

if (isSupabaseConfigured()) {
  try {
    _supabase = createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        storageKey: "careerpilot.supabase_session",
      },
    });
  } catch {
    _supabase = null;
  }
}

export function getSupabase(): SupabaseClient | null {
  return _supabase;
}

/** Convenience export — only valid when `isSupabaseConfigured()` is true. */
export const supabase = _supabase;
