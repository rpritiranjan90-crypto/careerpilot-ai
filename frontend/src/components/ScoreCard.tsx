export interface ScoreCardProps {
  score: number;
  label: string;
  maxScore?: number;
  subtitle?: string;
}

/**
 * Premium Score display card with percentage meter and semantic badges.
 * - 80-100: Emerald (Excellent / Strong)
 * - 60-79: Blue (Good / On Track)
 * - 40-59: Amber (Needs Improvement)
 * - 0-39: Rose (Critical Attention)
 */
export function ScoreCard({
  score,
  label,
  maxScore = 100,
  subtitle,
}: ScoreCardProps) {
  const percentage = Math.min(100, Math.max(0, (score / maxScore) * 100));

  let colorScheme = {
    bg: "bg-rose-50/60 border-rose-200/80",
    text: "text-rose-700",
    bar: "bg-rose-500",
    badge: "bg-rose-100 text-rose-800",
    status: "Needs Work",
  };

  if (percentage >= 80) {
    colorScheme = {
      bg: "bg-emerald-50/60 border-emerald-200/80",
      text: "text-emerald-700",
      bar: "bg-emerald-500",
      badge: "bg-emerald-100 text-emerald-800",
      status: "Strong",
    };
  } else if (percentage >= 60) {
    colorScheme = {
      bg: "bg-blue-50/60 border-blue-200/80",
      text: "text-blue-700",
      bar: "bg-blue-500",
      badge: "bg-blue-100 text-blue-800",
      status: "Good",
    };
  } else if (percentage >= 40) {
    colorScheme = {
      bg: "bg-amber-50/60 border-amber-200/80",
      text: "text-amber-700",
      bar: "bg-amber-500",
      badge: "bg-amber-100 text-amber-800",
      status: "In Progress",
    };
  }

  return (
    <div
      className={`rounded-2xl p-5 border transition-all duration-200 ${colorScheme.bg} shadow-2xs hover:shadow-xs`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
          {label}
        </span>
        <span
          className={`px-2 py-0.5 rounded-full text-[11px] font-bold ${colorScheme.badge}`}
        >
          {colorScheme.status}
        </span>
      </div>

      <div className="flex items-baseline gap-1 my-1">
        <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
          {score}
        </span>
        <span className="text-sm font-medium text-slate-400">/{maxScore}</span>
      </div>

      {/* Progress track */}
      <div className="w-full bg-slate-200/70 h-2 rounded-full mt-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${colorScheme.bar}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {subtitle && (
        <p className="text-xs text-slate-500 mt-2 font-medium leading-relaxed">
          {subtitle}
        </p>
      )}
    </div>
  );
}