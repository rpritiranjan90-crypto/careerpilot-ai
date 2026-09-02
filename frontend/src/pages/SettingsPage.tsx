import { useState } from "react";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Badge } from "../components/Badge";
import { useAuth } from "../hooks/useAuth";
import { deleteAccount } from "../services/api";

/**
 * Settings Page - Profile, Privacy, Local AI Setup & GDPR Article 17 Erasure.
 */
export function SettingsPage() {
  const { user, signOut } = useAuth();
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleteMessage, setDeleteMessage] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleDeleteAccount = async () => {
    setDeleting(true);
    setDeleteError(null);
    try {
      const res = await deleteAccount();
      if (res.error) {
        setDeleteError(res.error);
        setDeleting(false);
      } else {
        setDeleteMessage("Your account and all associated data have been permanently erased.");
        setTimeout(() => {
          signOut();
          window.location.href = "/";
        }, 2000);
      }
    } catch {
      setDeleteError("Failed to delete account. Please try again.");
      setDeleting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <header>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Settings
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Manage your account profile, privacy settings, local AI options, and data retention.
        </p>
      </header>

      {/* Account Profile */}
      <Card title="Account Profile">
        <div className="space-y-3 text-sm text-slate-700">
          <div className="flex items-center justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500 font-semibold text-xs uppercase tracking-wider">
              User ID:
            </span>
            <span className="font-mono bg-slate-100 text-slate-800 px-2.5 py-1 rounded-lg text-xs font-semibold">
              {user?.userId || "Guest / Anonymous"}
            </span>
          </div>
          {user?.email && (
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500 font-semibold text-xs uppercase tracking-wider">
                Email:
              </span>
              <span className="text-slate-900 font-medium text-xs sm:text-sm">
                {user.email}
              </span>
            </div>
          )}
          <div className="flex items-center justify-between py-2">
            <span className="text-slate-500 font-semibold text-xs uppercase tracking-wider">
              Account Status:
            </span>
            <Badge variant="success" size="sm">Active (Free Tier)</Badge>
          </div>
        </div>
      </Card>

      {/* Privacy & GDPR Right to Erasure */}
      <Card
        title="Data & Privacy (GDPR Article 17)"
        badge={<Badge variant="primary" size="sm">Compliant</Badge>}
      >
        <div className="space-y-4 text-sm text-slate-700">
          <div className="space-y-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
            <p>
              <strong className="text-slate-900">Resume Data:</strong> Resumes and extracted text are encrypted and stored in your private workspace.
            </p>
            <p>
              <strong className="text-slate-900">Job Descriptions & Interviews:</strong> Securely isolated to your account.
            </p>
            <p>
              <strong className="text-slate-900">Right to Erasure:</strong> Under GDPR Article 17, you can permanently delete your entire account, all database entries, and physical disk files with a single action.
            </p>
          </div>

          {deleteMessage && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs sm:text-sm font-semibold flex items-center gap-2">
              <span className="text-emerald-600">✓</span> {deleteMessage}
            </div>
          )}

          {deleteError && (
            <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs sm:text-sm font-semibold flex items-center gap-2">
              <span className="text-rose-600">⚠</span> {deleteError}
            </div>
          )}

          <div className="pt-4 border-t border-slate-100">
            {!confirmDelete ? (
              <Button
                variant="secondary"
                onClick={() => setConfirmDelete(true)}
                className="text-rose-600 border-rose-200 hover:bg-rose-50 hover:border-rose-300"
              >
                Delete My Account & All Personal Data
              </Button>
            ) : (
              <div className="p-5 bg-rose-50/80 border border-rose-200 rounded-2xl space-y-3 animate-in fade-in duration-150">
                <div className="flex items-center gap-2 text-rose-900 font-bold text-sm">
                  <span>⚠️</span>
                  <span>Are you sure? This action is permanent and cannot be undone.</span>
                </div>
                <p className="text-rose-700 text-xs leading-relaxed">
                  All resumes, uploaded documents on disk, job match assessments, and interview evaluations will be permanently and irreversibly purged.
                </p>
                <div className="flex flex-wrap gap-2 pt-2">
                  <button
                    type="button"
                    onClick={handleDeleteAccount}
                    disabled={deleting}
                    className="px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 disabled:opacity-50 transition-colors shadow-2xs"
                  >
                    {deleting ? "Deleting..." : "Yes, Permanently Delete Everything"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDelete(false)}
                    disabled={deleting}
                    className="px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-xl text-xs font-bold hover:bg-slate-50 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Free Tier & Local AI Setup */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Free Tier Architecture">
          <div className="space-y-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
            <p className="font-semibold text-slate-900">CareerPilot AI is free-first & open:</p>
            <ul className="space-y-1.5 pt-1">
              <li className="flex items-center gap-2">
                <span className="text-blue-600">✓</span> Zero mandatory cloud subscriptions
              </li>
              <li className="flex items-center gap-2">
                <span className="text-blue-600">✓</span> Private local inference via Ollama
              </li>
              <li className="flex items-center gap-2">
                <span className="text-blue-600">✓</span> Instant deterministic rule-based fallback
              </li>
            </ul>
          </div>
        </Card>

        <Card title="Local AI Setup (Ollama)">
          <div className="space-y-2 text-xs text-slate-600 leading-relaxed">
            <p>Run full private AI locally on your device:</p>
            <ol className="list-decimal list-inside space-y-1 pt-1 font-mono text-[11px] text-slate-700">
              <li>
                Download from{" "}
                <a
                  href="https://ollama.ai"
                  className="text-blue-600 hover:underline font-bold"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  ollama.ai
                </a>
              </li>
              <li>
                <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-800">
                  ollama pull llama3.2:3b
                </code>
              </li>
              <li>Launch backend / docker container</li>
            </ol>
          </div>
        </Card>
      </div>
    </div>
  );
}