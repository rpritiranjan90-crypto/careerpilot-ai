import { useState } from "react";
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
  const { signInWithEmail, signUpWithEmail, user, isSupabaseAuth } = useAuth();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
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
              disabled={loading}
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
      </Card>
    </div>
  );
}
