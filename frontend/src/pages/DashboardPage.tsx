import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "../components/Card";
import { ScoreCard } from "../components/ScoreCard";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { useAuth } from "../hooks/useAuth";
import { getUserDashboard, type DashboardResponse } from "../services/api";

/**
 * Career Readiness Dashboard Page - The User's Career Command Center
 */
export function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    const res = await getUserDashboard();
    if (res.error) {
      setError(res.error);
    } else if (res.data) {
      setData(res.data);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const userName = user?.email
    ? user.email.split("@")[0]
    : user?.userId || "Explorer";

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="relative">
          <div className="w-12 h-12 rounded-full border-3 border-blue-100 border-t-blue-600 animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-2.5 h-2.5 rounded-full bg-blue-600" />
          </div>
        </div>
        <p className="text-slate-600 font-semibold text-sm">
          Loading career readiness data...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-rose-100 text-rose-600 mb-4 shadow-2xs">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-6 h-6">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Unable to Load Dashboard</h2>
        <p className="text-slate-500 text-sm mb-6">{error}</p>
        <button
          onClick={fetchDashboard}
          className="px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors shadow-xs"
        >
          Try Again
        </button>
      </div>
    );
  }

  const hasData = Boolean(data?.has_data);
  const cr = data?.career_readiness;

  // --- Welcoming Empty State ---
  if (!hasData || !cr) {
    return (
      <div className="max-w-3xl mx-auto space-y-8 py-6">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 mb-2 shadow-xs border border-blue-100">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-8 h-8">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Career Readiness Dashboard
          </h1>
          <p className="text-sm sm:text-base text-slate-500 max-w-lg mx-auto leading-relaxed">
            Welcome to CareerPilot 👋 Your career readiness score and hiring metrics will appear here once you complete your first activity.
          </p>
        </div>

        {/* 3 Step Getting Started Cards */}
        <div className="grid gap-4 sm:grid-cols-3 pt-2">
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 flex flex-col justify-between hover:shadow-xs transition-shadow">
            <div>
              <span className="text-xs font-bold text-blue-600 block mb-1">Step 1</span>
              <h3 className="font-bold text-slate-900 mb-1">Upload Resume</h3>
              <p className="text-xs text-slate-500 leading-relaxed mb-4">
                Extract skills and audit strengths to establish your baseline score.
              </p>
            </div>
            <Link
              to="/resume"
              className="w-full text-center py-2 px-3 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 shadow-2xs transition-colors"
            >
              Analyze Resume
            </Link>
          </div>

          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 flex flex-col justify-between hover:shadow-xs transition-shadow">
            <div>
              <span className="text-xs font-bold text-slate-400 block mb-1">Step 2</span>
              <h3 className="font-bold text-slate-900 mb-1">Match Target Job</h3>
              <p className="text-xs text-slate-500 leading-relaxed mb-4">
                Compare your qualifications against target job descriptions.
              </p>
            </div>
            <Link
              to="/job-match"
              className="w-full text-center py-2 px-3 bg-white border border-slate-200 text-slate-700 rounded-xl text-xs font-bold hover:bg-slate-50 transition-colors"
            >
              Match Job Description
            </Link>
          </div>

          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 flex flex-col justify-between hover:shadow-xs transition-shadow">
            <div>
              <span className="text-xs font-bold text-slate-400 block mb-1">Step 3</span>
              <h3 className="font-bold text-slate-900 mb-1">Mock Interview</h3>
              <p className="text-xs text-slate-500 leading-relaxed mb-4">
                Rehearse technical and HR questions to polish your answers.
              </p>
            </div>
            <Link
              to="/interview"
              className="w-full text-center py-2 px-3 bg-white border border-slate-200 text-slate-700 rounded-xl text-xs font-bold hover:bg-slate-50 transition-colors"
            >
              Practice Interview
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // --- Populated Career Command Center ---
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Personalized Greeting */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/80 pb-6">
        <div>
          <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
            Career Command Center
          </span>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight mt-0.5">
            Welcome back, {userName}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time composite metrics aggregated across all your career preparation activities.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-center">
          <Badge variant="success" size="md">
            ● Live Sync
          </Badge>
        </div>
      </header>

      {/* Main Readiness Gauge & Next Best Action Hero Card */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Overall Score Card */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col items-center justify-center text-center">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
            Overall Readiness
          </span>
          <div className="flex items-baseline gap-1 my-1">
            <span className="text-6xl font-extrabold text-blue-600 tracking-tight">
              {cr.overall_score}
            </span>
            <span className="text-xl font-semibold text-slate-400">/100</span>
          </div>
          <p className="text-xs font-semibold text-slate-600 mt-1">
            Career Readiness Score
          </p>
          <div className="w-full bg-slate-100 h-2.5 rounded-full mt-4 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full transition-all duration-700"
              style={{ width: `${cr.overall_score}%` }}
            />
          </div>
        </div>

        {/* Highlighted Next Best Action Card */}
        <div className="md:col-span-2 bg-gradient-to-br from-blue-50/80 via-indigo-50/50 to-white border border-blue-200/80 rounded-2xl p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 rounded-md bg-blue-600 text-white text-[11px] font-bold">
                Next Best Action
              </span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              {cr.recommended_next_step}
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 mt-1.5 leading-relaxed">
              Addressing your highest priority skill gaps or practicing targeted interview questions will yield the largest increase in overall hiring readiness.
            </p>
          </div>

          <div className="pt-4 flex flex-wrap gap-2">
            <Link to="/improve">
              <Button size="sm">
                Open Improvement Plan ➔
              </Button>
            </Link>
            <Link to="/job-match">
              <Button variant="secondary" size="sm">
                View Skill Gaps
              </Button>
            </Link>
            <Link to="/interview">
              <Button variant="secondary" size="sm">
                Practice Questions
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* 4 KPI Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
        <ScoreCard
          score={cr.breakdown.resume.score}
          label="Resume Quality"
          subtitle="30% Readiness Weight"
        />
        <ScoreCard
          score={cr.breakdown.job_match.score}
          label="Job Match"
          subtitle="25% Readiness Weight"
        />
        <ScoreCard
          score={cr.breakdown.interview.score}
          label="Interview Skills"
          subtitle="25% Readiness Weight"
        />
        <ScoreCard
          score={cr.breakdown.skills.score}
          label="Skill Coverage"
          subtitle="20% Readiness Weight"
        />
      </div>

      {/* Strengths & Priority Focus 2-Column Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card
          title="Strongest Area"
          badge={<Badge variant="success" size="sm">🏆 Top Metric</Badge>}
        >
          <div className="flex items-center gap-4 py-2">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl font-bold shrink-0 border border-emerald-100">
              ✓
            </div>
            <div>
              <p className="font-bold text-slate-900 text-base sm:text-lg">
                {cr.strongest_area.label}
              </p>
              <p className="text-xs sm:text-sm text-slate-500">
                Performance Score: <span className="font-bold text-emerald-700">{cr.strongest_area.score}%</span>
              </p>
            </div>
          </div>
        </Card>

        <Card
          title="Priority Focus Area"
          badge={<Badge variant="warning" size="sm">📈 High Leverage</Badge>}
        >
          <div className="flex items-center gap-4 py-2">
            <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center text-xl font-bold shrink-0 border border-amber-100">
              !
            </div>
            <div>
              <p className="font-bold text-slate-900 text-base sm:text-lg">
                {cr.needs_improvement.label}
              </p>
              <p className="text-xs sm:text-sm text-slate-500">
                Performance Score: <span className="font-bold text-amber-700">{cr.needs_improvement.score}%</span>
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Activity Counters Summary */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs">
        <h3 className="text-sm font-bold text-slate-900 mb-4">Activity Summary</h3>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-2xl font-extrabold text-slate-900">{data.resume_count}</div>
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mt-0.5">Resumes</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-2xl font-extrabold text-slate-900">{data.job_match_count}</div>
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mt-0.5">Job Matches</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-2xl font-extrabold text-slate-900">{data.interview_count}</div>
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mt-0.5">Interviews</div>
          </div>
        </div>
      </div>

      {/* Quick Action Shortcuts */}
      <div className="flex flex-wrap gap-3 justify-center pt-2">
        <Link to="/resume">
          <Button size="md" className="shadow-2xs">
            Analyze Resume
          </Button>
        </Link>
        <Link to="/job-match">
          <Button variant="secondary" size="md">
            Assess Job Match
          </Button>
        </Link>
        <Link to="/interview">
          <Button variant="secondary" size="md">
            Mock Interview
          </Button>
        </Link>
      </div>
    </div>
  );
}