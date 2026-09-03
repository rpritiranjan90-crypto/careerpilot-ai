import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ErrorState } from "../components/States";

/**
 * CareerPilot AI - Production Sign-in & Registration page.
 * Supports genuine Supabase email/password authentication and account creation.
 */
export function LoginPage() {
  const navigate = useNavigate();
  const { signInWithEmail, signUpWithEmail, signInWithOAuth, user, isSupabaseAuth } = useAuth();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState<"google" | "github" | null>(null);

  const handleOAuth = async (provider: "google" | "github") => {
    setError(null);
    setInfoMessage(null);
    setOauthLoading(provider);
    const res = await signInWithOAuth(provider);
    setOauthLoading(null);
    if (!res.ok) {
      setError(res.error || `Unable to authenticate with ${provider}.`);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setInfoMessage(null);
    setLoading(true);

    if (mode === "signin") {
      const result = await signInWithEmail(email, password);
      setLoading(false);
      if (result.ok) {
        navigate("/resume");
      } else {
        setError(result.error || "Sign-in failed. Please try again.");
      }
    } else {
      const result = await signUpWithEmail(email, password);
      setLoading(false);
      if (result.ok) {
        if (result.message) {
          setInfoMessage(result.message);
        } else {
          navigate("/resume");
        }
      } else {
        setError(result.error || "Account registration failed. Please try again.");
      }
    }
  };

  // If already signed in, redirect to the resume page
  if (user) {
    navigate("/resume");
    return null;
  }

  return (
    <div className="max-w-md mx-auto py-8 sm:py-12">
      {/* Brand Header */}
      <div className="text-center mb-8">
        <Link to="/" className="inline-flex items-center gap-2 mb-4">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-xs">
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </Link>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Welcome to CareerPilot
        </h1>
        <p className="text-sm text-slate-500 mt-2">
          {mode === "signin"
            ? "Sign in to access your career readiness dashboard and prep tools."
            : "Create your free account to unlock personalized career coaching."}
        </p>
      </div>

      {/* Mode Switcher Tabs */}
      <div className="flex p-1 bg-slate-100/90 rounded-xl mb-6 border border-slate-200/80">
        <button
          type="button"
          onClick={() => {
            setMode("signin");
            setError(null);
            setInfoMessage(null);
          }}
          className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
            mode === "signin"
              ? "bg-white text-slate-900 shadow-xs"
              : "text-slate-500 hover:text-slate-900"
          }`}
        >
          Sign In
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("signup");
            setError(null);
            setInfoMessage(null);
          }}
          className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
            mode === "signup"
              ? "bg-white text-slate-900 shadow-xs"
              : "text-slate-500 hover:text-slate-900"
          }`}
        >
          Create Account
        </button>
      </div>

      {infoMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200/80 text-xs text-emerald-800 font-medium mb-6 flex items-start gap-2">
          <span className="text-sm font-bold">✓</span>
          <span>{infoMessage}</span>
        </div>
      )}

      {error && <ErrorState message={error} className="mb-6" />}

      <Card>
        <div className="space-y-4">
          {/* Social OAuth Providers */}
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              disabled={Boolean(oauthLoading) || loading}
              onClick={() => handleOAuth("google")}
              className="inline-flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 active:bg-slate-100 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-50"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#EA4335"
                  d="M12 5c1.7 0 3 .6 4 1.5l3-3C17.2 1.8 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.4 9 5 12 5z"
                />
                <path
                  fill="#4285F4"
                  d="M23.5 12.3c0-.8-.1-1.7-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.6 14.8c-.3-.8-.4-1.8-.4-2.8s.1-2 .4-2.8L1.9 6.3C.7 8.7 0 10.3 0 12s.7 3.3 1.9 5.7l3.7-2.9z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.4-6.4-5.2L1.9 16C3.7 19.7 7.5 23 12 23z"
                />
              </svg>
              {oauthLoading === "google" ? "Connecting..." : "Google"}
            </button>

            <button
              type="button"
              disabled={Boolean(oauthLoading) || loading}
              onClick={() => handleOAuth("github")}
              className="inline-flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 active:bg-slate-100 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-50"
            >
              <svg className="w-4 h-4 fill-slate-800" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
              {oauthLoading === "github" ? "Connecting..." : "GitHub"}
            </button>
          </div>

          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-slate-200" />
            <span className="flex-shrink mx-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              or use email
            </span>
            <div className="flex-grow border-t border-slate-200" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5"
              >
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (error) setError(null);
                }}
                autoComplete="email"
                placeholder="e.g. name@example.com"
                className="block w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                required
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="password"
                  className="block text-xs font-bold uppercase tracking-wider text-slate-700"
                >
                  Password
                </label>
                {isSupabaseAuth ? (
                  <span className="text-[11px] text-slate-400 font-medium">
                    {mode === "signup" ? "Min. 6 characters" : "Supabase Auth"}
                  </span>
                ) : (
                  <span className="text-[11px] text-slate-400 font-medium">
                    Dev Ready
                  </span>
                )}
              </div>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (error) setError(null);
                }}
                autoComplete={mode === "signin" ? "current-password" : "new-password"}
                placeholder="••••••••"
                className="block w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                required
              />
            </div>

            <div className="pt-2">
              <Button
                type="submit"
                disabled={loading || Boolean(oauthLoading)}
                size="lg"
                className="w-full shadow-xs"
              >
                {loading
                  ? mode === "signin"
                    ? "Signing in..."
                    : "Creating account..."
                  : mode === "signin"
                  ? "Sign in to CareerPilot"
                  : "Create Account"}
              </Button>
            </div>

            <p className="text-center text-xs text-slate-400 pt-2">
              By continuing, you agree to CareerPilot AI terms and GDPR privacy policies.
            </p>
          </form>
        </div>
      </Card>
    </div>
  );
}
