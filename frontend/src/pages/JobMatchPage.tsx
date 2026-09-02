import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ScoreCard } from "../components/ScoreCard";
import { Badge } from "../components/Badge";
import { LoadingState, ErrorState } from "../components/States";
import { matchJob, type JobMatch } from "../services/api";

/**
 * Job Match Page - 3-Step Intelligent Skill-Gap Analysis
 */
export function JobMatchPage() {
  const [resumeSkills, setResumeSkills] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState<JobMatch | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleMatch = async () => {
    const skills = resumeSkills
      .split(/[,\n]/)
      .map((s) => s.trim())
      .filter(Boolean);

    if (skills.length === 0) {
      setError("Please list at least one skill from your resume.");
      return;
    }
    if (jobDescription.trim().length < 50) {
      setError("Please paste a job description (at least 50 characters).");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await matchJob(skills, jobDescription);
      if (res.error) {
        setError(res.error);
        return;
      }
      setResult(res.data!);
    } catch {
      setError("Match calculation failed. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResumeSkills("");
    setJobDescription("");
    setResult(null);
    setError(null);
  };

  if (loading) {
    return (
      <LoadingState
        message="Comparing your skills with this role..."
        subMessage="Extracting employer requirements, calculating semantic skill overlap, and prioritizing gaps."
      />
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <header className="text-center mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Job Match & Skill-Gap Analysis
        </h1>
        <p className="text-sm sm:text-base text-slate-500 mt-2 max-w-xl mx-auto">
          Compare your verified skills directly against any target job description to discover exact alignment and missing requirements.
        </p>
      </header>

      {error && <ErrorState message={error} />}

      {!result ? (
        <div className="space-y-6">
          {/* 3-Step Process Header */}
          <div className="grid grid-cols-3 gap-2 sm:gap-4 text-center">
            <div className="p-3 rounded-xl bg-blue-50 border border-blue-200/80">
              <span className="text-[11px] font-bold text-blue-600 uppercase tracking-wider block">
                Step 1
              </span>
              <span className="text-xs sm:text-sm font-bold text-slate-900">Your Skills</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Step 2
              </span>
              <span className="text-xs sm:text-sm font-bold text-slate-900">Target Role</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Step 3
              </span>
              <span className="text-xs sm:text-sm font-bold text-slate-900">AI Match</span>
            </div>
          </div>

          <Card
            title="Compare With a Job"
            description="List your skills and paste the job description below."
          >
            <div className="space-y-5">
              <div>
                <label
                  htmlFor="skills"
                  className="block text-sm font-bold text-slate-900 mb-1.5"
                >
                  Your skills (comma or newline separated)
                </label>
                <textarea
                  id="skills"
                  value={resumeSkills}
                  onChange={(e) => setResumeSkills(e.target.value)}
                  rows={3}
                  placeholder="Python, SQL, React, TypeScript, Docker, AWS"
                  className="block w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="job-desc"
                    className="block text-sm font-bold text-slate-900"
                  >
                    Job description
                  </label>
                  <span className={`text-xs font-mono font-medium ${
                    jobDescription.length >= 50 ? "text-emerald-600" : "text-slate-400"
                  }`}>
                    {jobDescription.length} characters (min 50)
                  </span>
                </div>
                <textarea
                  id="job-desc"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  rows={8}
                  placeholder="Paste the target job description or requirements here..."
                  className="block w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>

              <Button
                onClick={handleMatch}
                size="lg"
                disabled={resumeSkills.trim() === "" || jobDescription.trim().length < 50}
                className="w-full sm:w-auto"
              >
                Check Job Match
              </Button>
            </div>
          </Card>
        </div>
      ) : (
        <JobMatchResults result={result} onReset={handleReset} />
      )}
    </div>
  );
}

interface JobMatchResultsProps {
  result: JobMatch;
  onReset: () => void;
}

function JobMatchResults({ result, onReset }: JobMatchResultsProps) {
  const matched = result.matched_skills.filter((m) => m.matched);

  return (
    <div className="space-y-6">
      {/* Match Score Card */}
      <Card>
        <div className="flex items-center justify-between flex-wrap gap-6">
          <div className="space-y-1.5 max-w-xl">
            <div className="flex items-center gap-2">
              <Badge variant="primary" size="md">Match Assessment</Badge>
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              Estimated Match
            </h2>
            <p className="text-sm text-slate-600 leading-relaxed">{result.summary}</p>
          </div>
          <div className="shrink-0 w-full sm:w-48">
            <ScoreCard score={result.match_score} label="Match %" />
          </div>
        </div>
      </Card>

      {/* Skills Comparison 2-Column Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card
          title="Matched Skills"
          badge={<Badge variant="success" size="sm">✓ {matched.length} Matched</Badge>}
          description="Skills found in both your profile and the job description."
        >
          {matched.length > 0 ? (
            <div className="flex flex-wrap gap-2 pt-1">
              {matched.map((m, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200/80 shadow-2xs"
                >
                  <span className="font-bold text-emerald-600" aria-hidden="true">✓</span>
                  <span>{m.skill}</span>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No direct skills matched yet.</p>
          )}
        </Card>

        <Card
          title="Skills to Develop"
          badge={<Badge variant="warning" size="sm">✕ {result.missing_skills.length} Gaps</Badge>}
          description="Required skills not yet detected in your profile."
        >
          {result.missing_skills.length > 0 ? (
            <div className="flex flex-wrap gap-2 pt-1">
              {result.missing_skills.map((s, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200/80 shadow-2xs"
                >
                  <span className="font-bold text-amber-600" aria-hidden="true">✕</span>
                  <span>{s}</span>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-emerald-600 font-semibold">
              ✓ All key job requirements match your profile!
            </p>
          )}
        </Card>
      </div>

      {/* Recommendations */}
      {result.recommendations.length > 0 && (
        <Card
          title="Recommended Next Steps"
          description="Actionable advice to bridge the gap and prepare for interviews for this role."
        >
          <ul className="space-y-3 pt-1">
            {result.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700 leading-relaxed">
                <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5" aria-hidden="true">
                  →
                </span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Action Footer */}
      <div className="flex flex-col sm:flex-row gap-3 justify-center items-center pt-4">
        <Button variant="secondary" onClick={onReset} className="w-full sm:w-auto">
          Try Another Job
        </Button>
        <Link to="/improve#skills" className="w-full sm:w-auto">
          <Button variant="secondary" className="w-full sm:w-auto border-blue-200 text-blue-700 bg-blue-50/50 hover:bg-blue-100/60">
            Bridge Skill Gaps ➔
          </Button>
        </Link>
        <Link to="/interview" className="w-full sm:w-auto">
          <Button className="w-full sm:w-auto">
            Practice Interview →
          </Button>
        </Link>
      </div>
    </div>
  );
}
