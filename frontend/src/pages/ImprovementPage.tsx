import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "../components/Card";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { LoadingState, ErrorState } from "../components/States";
import {
  getImprovementPlan,
  refreshImprovementPlan,
  toggleActionItem,
  type CareerImprovementPlan,
  type ActionItem,
} from "../services/api";

/**
 * Career Improvement Page - Actionable AI Career Coach.
 *
 * Provides concrete Before/After resume rewrites, prioritized skill learning paths,
 * a Today/This Week/This Month checklist, and verified historical progress tracking.
 */
export function ImprovementPage() {
  const [plan, setPlan] = useState<CareerImprovementPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [togglingTaskId, setTogglingTaskId] = useState<string | null>(null);

  const fetchPlan = async () => {
    setLoading(true);
    setError(null);
    const res = await getImprovementPlan();
    if (res.error) {
      setError(res.error);
    } else if (res.data) {
      setPlan(res.data);
    }
    setLoading(false);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    const res = await refreshImprovementPlan();
    if (res.error) {
      setError(res.error);
    } else if (res.data) {
      setPlan(res.data);
    }
    setRefreshing(false);
  };

  const handleToggleTask = async (taskId: string) => {
    if (!plan) return;
    setTogglingTaskId(taskId);

    // Optimistic UI update
    const updateTimeline = (items: ActionItem[]) =>
      items.map((item) =>
        item.task_id === taskId
          ? { ...item, is_completed: !item.is_completed }
          : item
      );

    setPlan({
      ...plan,
      action_plan: {
        today: updateTimeline(plan.action_plan.today),
        this_week: updateTimeline(plan.action_plan.this_week),
        this_month: updateTimeline(plan.action_plan.this_month),
      },
    });

    const res = await toggleActionItem(taskId);
    setTogglingTaskId(null);

    if (res.error) {
      // Revert if error
      fetchPlan();
    }
  };

  const handleCopyText = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  useEffect(() => {
    fetchPlan();
  }, []);

  if (loading) {
    return (
      <LoadingState
        message="Generating your personalized improvement roadmap..."
        subMessage="Auditing resume weaknesses, benchmarking missing role skills, and compiling action plans."
      />
    );
  }

  if (error) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <ErrorState
          title="Unable to Load Improvement Plan"
          message={error}
          action={
            <Button onClick={fetchPlan} size="sm">
              Try Again
            </Button>
          }
        />
      </div>
    );
  }

  // --- Onboarding / Empty State ---
  if (!plan || !plan.has_data) {
    return (
      <div className="max-w-3xl mx-auto space-y-8 py-6">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 mb-2 shadow-xs border border-blue-100">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-8 h-8">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Career Improvement Plan
          </h1>
          <p className="text-sm sm:text-base text-slate-500 max-w-lg mx-auto leading-relaxed">
            Your personalized AI career coaching plan will appear here once you upload your resume or match a target role.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3 pt-2">
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 flex flex-col justify-between">
            <div>
              <span className="text-xs font-bold text-blue-600 block mb-1">Step 1</span>
              <h3 className="font-bold text-slate-900 mb-1">Upload Resume</h3>
              <p className="text-xs text-slate-500 leading-relaxed mb-4">
                Receive concrete Before/After rewrite suggestions with ATS metrics.
              </p>
            </div>
            <Link
              to="/resume"
              className="w-full text-center py-2 px-3 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 shadow-2xs transition-colors"
            >
              Upload Resume
            </Link>
          </div>

          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 flex flex-col justify-between">
            <div>
              <span className="text-xs font-bold text-slate-400 block mb-1">Step 2</span>
              <h3 className="font-bold text-slate-900 mb-1">Match Target Job</h3>
              <p className="text-xs text-slate-500 leading-relaxed mb-4">
                Unlock exact skill-gap roadmaps and hands-on exercises for your target role.
              </p>
            </div>
            <Link
              to="/job-match"
              className="w-full text-center py-2 px-3 bg-white border border-slate-200 text-slate-700 rounded-xl text-xs font-bold hover:bg-slate-50 transition-colors"
            >
              Match Job Description
            </Link>
          </div>

          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 flex flex-col justify-between">
            <div>
              <span className="text-xs font-bold text-slate-400 block mb-1">Step 3</span>
              <h3 className="font-bold text-slate-900 mb-1">Mock Interview</h3>
              <p className="text-xs text-slate-500 leading-relaxed mb-4">
                Practice technical drills to prepare for high-stakes interviews.
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

  const nba = plan.next_best_action;
  const pt = plan.progress_tracking;

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Top Header */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="primary" size="md">
              AI Career Coach
            </Badge>
            {plan.data_completeness === "resume_only" && (
              <Badge variant="warning" size="sm">
                Resume Only (Add Job Match for Exact Gaps)
              </Badge>
            )}
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Career Improvement Plan
          </h1>
          <p className="text-sm text-slate-500 mt-1 max-w-2xl">
            {plan.summary}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 self-start sm:self-center shrink-0">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => window.print()}
            className="gap-1.5"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Print / Save as PDF
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleRefresh}
            loading={refreshing}
          >
            🔄 Refresh Plan & Snapshot
          </Button>
        </div>
      </header>

      {/* Hero Section: Improvement Score & Next Best Action */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Score Target Card */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col justify-between text-center">
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Readiness Improvement Target
            </span>
            <div className="flex items-center justify-center gap-2 my-2">
              <span className="text-4xl font-black text-slate-900">
                {plan.overall_score}
              </span>
              <span className="text-slate-400 font-bold text-lg">➔</span>
              <span className="text-4xl font-black text-blue-600">
                {plan.target_potential_score}
              </span>
            </div>
            <span className="inline-block px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/80">
              +{plan.target_potential_score - plan.overall_score} pts Potential Boost
            </span>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500 leading-relaxed">
            Follow the prioritized roadmap below to unlock your maximum hiring conversion score.
          </div>
        </div>

        {/* Exactly One High-Leverage Next Best Action Hero Card */}
        {nba && (
          <div className="md:col-span-2 bg-gradient-to-br from-blue-50/90 via-indigo-50/50 to-white border border-blue-200/90 rounded-2xl p-6 shadow-xs flex flex-col justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-md bg-blue-600 text-white text-[11px] font-bold">
                  Next Best Action
                </span>
                <span className="text-xs font-semibold text-blue-700 capitalize">
                  {nba.category} Focus
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                {nba.title}
              </h2>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                <strong className="text-slate-900">Why: </strong>{nba.why}
              </p>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                <strong className="text-slate-900">What to do: </strong>{nba.what_to_do}
              </p>
              <p className="text-xs text-emerald-700 font-medium pt-1">
                ✓ <strong>Expected Outcome: </strong>{nba.expected_outcome}
              </p>
            </div>

            <div className="pt-4 flex items-center gap-3">
              <Link to={nba.cta_link}>
                <Button size="md">
                  {nba.cta_label} →
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* SECTION 1: Resume Enhancements (Concrete Before / After Rewrites) */}
      <section className="space-y-4" id="resume">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <span>📄 Resume Enhancements</span>
              <Badge variant="primary" size="sm">{plan.resume_enhancements.length} Suggestions</Badge>
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Concrete phrasing improvements with explicit [X] metric placeholders.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {plan.resume_enhancements.map((enhancement) => (
            <Card
              key={enhancement.id}
              className="border-slate-200/90"
              badge={
                <Badge
                  variant={
                    enhancement.severity === "high"
                      ? "error"
                      : enhancement.severity === "medium"
                      ? "warning"
                      : "neutral"
                  }
                  size="sm"
                >
                  {enhancement.severity.toUpperCase()} PRIORITY
                </Badge>
              }
              title={enhancement.category}
              description={enhancement.issue}
            >
              <div className="space-y-4 pt-2">
                <div className="p-3 rounded-xl bg-slate-50 text-xs text-slate-600 leading-relaxed">
                  <strong className="text-slate-800">Why this matters: </strong>
                  {enhancement.explanation}
                </div>

                {/* Before / After Comparison */}
                <div className="grid gap-3 sm:grid-cols-2">
                  {/* Before */}
                  <div className="p-4 rounded-xl bg-rose-50/50 border border-rose-100 flex flex-col justify-between">
                    <div>
                      <span className="text-[11px] font-bold text-rose-700 uppercase tracking-wider block mb-1.5">
                        ✕ Weak / Unquantified Phrasing (Before)
                      </span>
                      <p className="text-xs text-slate-700 leading-relaxed font-mono">
                        "{enhancement.before_example}"
                      </p>
                    </div>
                  </div>

                  {/* After */}
                  <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-100 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">
                          ✓ Strong / Measurable Action (After)
                        </span>
                        {enhancement.is_placeholder_example && (
                          <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-bold">
                            Placeholder Template
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-800 leading-relaxed font-mono bg-white p-2.5 rounded-lg border border-emerald-100">
                        "{enhancement.after_example}"
                      </p>
                    </div>

                    <div className="pt-3 flex items-center justify-between">
                      <span className="text-[10px] text-slate-400 italic">
                        Replace [X] with your verified achievements.
                      </span>
                      <button
                        type="button"
                        onClick={() => handleCopyText(enhancement.after_example, enhancement.id)}
                        className="text-xs font-bold text-blue-600 hover:text-blue-700 px-2.5 py-1 rounded bg-white border border-blue-200 shadow-2xs hover:bg-blue-50 transition-colors"
                      >
                        {copiedId === enhancement.id ? "✓ Copied!" : "Copy Suggestion"}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* SECTION 2: Skill Gap Analysis & Learning Paths */}
      <section className="space-y-4" id="skills">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <span>🎯 Skill Gap Analysis & Learning Paths</span>
              <Badge variant="warning" size="sm">{plan.skill_gaps.length} Actionable Gaps</Badge>
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Targeted skills prioritized by real job match requirements with hands-on practice.
            </p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {plan.skill_gaps.map((gap, i) => (
            <Card
              key={i}
              className="border-slate-200/90 flex flex-col justify-between"
              title={gap.skill_name}
              badge={
                <Badge
                  variant={
                    gap.priority === "High"
                      ? "error"
                      : gap.priority === "Medium"
                      ? "warning"
                      : "neutral"
                  }
                  size="sm"
                >
                  {gap.priority} Priority
                </Badge>
              }
            >
              <div className="space-y-3 pt-2 text-xs text-slate-600">
                <p>
                  <strong className="text-slate-800">Reason: </strong>
                  {gap.reason}
                </p>

                {gap.prerequisites.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-semibold text-slate-700">Prerequisites:</span>
                    {gap.prerequisites.map((p, idx) => (
                      <span key={idx} className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">
                        {p}
                      </span>
                    ))}
                  </div>
                )}

                <div className="p-3 bg-blue-50/50 rounded-xl border border-blue-100/80">
                  <span className="font-bold text-blue-700 block mb-1">Learning Path:</span>
                  <p className="text-slate-700 leading-relaxed font-mono text-[11px]">
                    {gap.learning_path}
                  </p>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="font-bold text-slate-800 block mb-1">Hands-on Exercise:</span>
                  <p className="text-slate-700 leading-relaxed font-mono text-[11px]">
                    {gap.practical_exercise}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* SECTION 3: Personalized Action Plan (Persisted Checklist) */}
      <section className="space-y-4" id="action-plan">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <span>📅 Personalized Action Plan</span>
              <Badge variant="success" size="sm">Persisted in DB</Badge>
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Check off tasks as you complete them. Progress is saved automatically.
            </p>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {/* Today */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
                <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                  Today (Quick Wins)
                </span>
                <span className="text-xs text-slate-400 font-medium">15–30 mins</span>
              </div>

              <div className="space-y-3">
                {plan.action_plan.today.map((task) => (
                  <label
                    key={task.task_id}
                    className={`flex items-start gap-3 p-3 rounded-xl border transition-all cursor-pointer ${
                      task.is_completed
                        ? "bg-slate-50/80 border-slate-200 text-slate-400"
                        : "bg-white border-slate-200/80 hover:border-blue-300 text-slate-800 shadow-2xs"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={task.is_completed}
                      disabled={togglingTaskId === task.task_id}
                      onChange={() => handleToggleTask(task.task_id)}
                      className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 mt-0.5 cursor-pointer"
                    />
                    <div className="text-xs leading-relaxed flex-1">
                      <span className={task.is_completed ? "line-through" : "font-medium"}>
                        {task.task}
                      </span>
                      <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-400 font-mono">
                        <span>⏱ {task.estimated_minutes}m</span>
                        {task.is_completed && <span className="text-emerald-600 font-bold">✓ Done</span>}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* This Week */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
                <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">
                  This Week (Skills)
                </span>
                <span className="text-xs text-slate-400 font-medium">45–60 mins</span>
              </div>

              <div className="space-y-3">
                {plan.action_plan.this_week.map((task) => (
                  <label
                    key={task.task_id}
                    className={`flex items-start gap-3 p-3 rounded-xl border transition-all cursor-pointer ${
                      task.is_completed
                        ? "bg-slate-50/80 border-slate-200 text-slate-400"
                        : "bg-white border-slate-200/80 hover:border-indigo-300 text-slate-800 shadow-2xs"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={task.is_completed}
                      disabled={togglingTaskId === task.task_id}
                      onChange={() => handleToggleTask(task.task_id)}
                      className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 mt-0.5 cursor-pointer"
                    />
                    <div className="text-xs leading-relaxed flex-1">
                      <span className={task.is_completed ? "line-through" : "font-medium"}>
                        {task.task}
                      </span>
                      <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-400 font-mono">
                        <span>⏱ {task.estimated_minutes}m</span>
                        {task.is_completed && <span className="text-emerald-600 font-bold">✓ Done</span>}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* This Month */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  This Month (Projects)
                </span>
                <span className="text-xs text-slate-400 font-medium">Capstones</span>
              </div>

              <div className="space-y-3">
                {plan.action_plan.this_month.map((task) => (
                  <label
                    key={task.task_id}
                    className={`flex items-start gap-3 p-3 rounded-xl border transition-all cursor-pointer ${
                      task.is_completed
                        ? "bg-slate-50/80 border-slate-200 text-slate-400"
                        : "bg-white border-slate-200/80 hover:border-slate-400 text-slate-800 shadow-2xs"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={task.is_completed}
                      disabled={togglingTaskId === task.task_id}
                      onChange={() => handleToggleTask(task.task_id)}
                      className="w-4 h-4 rounded text-slate-900 focus:ring-slate-500 mt-0.5 cursor-pointer"
                    />
                    <div className="text-xs leading-relaxed flex-1">
                      <span className={task.is_completed ? "line-through" : "font-medium"}>
                        {task.task}
                      </span>
                      <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-400 font-mono">
                        <span>⏱ {task.estimated_minutes}m</span>
                        {task.is_completed && <span className="text-emerald-600 font-bold">✓ Done</span>}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: Real Historical Progress Tracking */}
      <section className="space-y-4" id="progress">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <span>📈 Verified Historical Progress</span>
              {pt.has_history ? (
                <Badge variant="success" size="sm">Verified Snapshot History</Badge>
              ) : (
                <Badge variant="neutral" size="sm">Baseline Established</Badge>
              )}
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              {pt.has_history
                ? "Actual verified score deltas calculated against previous database assessments."
                : "No previous assessment yet. Future analyses will display verified score improvements here."}
            </p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
          <ProgressCard
            label="Overall Readiness"
            current={pt.overall_readiness.current}
            previous={pt.overall_readiness.previous}
            delta={pt.overall_readiness.delta}
          />
          <ProgressCard
            label="Resume Score"
            current={pt.resume_score.current}
            previous={pt.resume_score.previous}
            delta={pt.resume_score.delta}
          />
          <ProgressCard
            label="Job Match Score"
            current={pt.job_match_score.current}
            previous={pt.job_match_score.previous}
            delta={pt.job_match_score.delta}
          />
          <ProgressCard
            label="Interview Score"
            current={pt.interview_score.current}
            previous={pt.interview_score.previous}
            delta={pt.interview_score.delta}
          />
        </div>
      </section>
    </div>
  );
}

interface ProgressCardProps {
  label: string;
  current: number;
  previous: number | null;
  delta: number | null;
}

function ProgressCard({ label, current, previous, delta }: ProgressCardProps) {
  return (
    <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">
        {label}
      </span>

      <div className="flex items-baseline gap-2 my-1">
        <span className="text-3xl font-black text-slate-900">{current}</span>
        <span className="text-xs text-slate-400 font-medium">/100</span>
      </div>

      <div className="pt-2 border-t border-slate-100 mt-2 flex items-center justify-between text-xs">
        {previous !== null && delta !== null ? (
          <>
            <span className="text-slate-500 font-mono">
              Prev: {previous}
            </span>
            <span
              className={`font-bold px-2 py-0.5 rounded-full text-[11px] ${
                delta > 0
                  ? "bg-emerald-50 text-emerald-700"
                  : delta < 0
                  ? "bg-rose-50 text-rose-700"
                  : "bg-slate-100 text-slate-700"
              }`}
            >
              {delta > 0 ? `+${delta}` : delta} pts
            </span>
          </>
        ) : (
          <span className="text-slate-400 text-[11px] italic">
            No previous assessment yet
          </span>
        )}
      </div>
    </div>
  );
}
