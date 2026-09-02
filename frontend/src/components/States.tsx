import { ReactNode } from "react";

export interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

/**
 * Clean, engaging empty state component.
 */
export function EmptyState({
  title,
  description,
  icon,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`text-center py-12 px-6 rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 ${className}`}
    >
      {icon ? (
        <div className="mx-auto w-12 h-12 text-slate-400 mb-3 flex items-center justify-center rounded-xl bg-white border border-slate-200/80 shadow-2xs">
          {icon}
        </div>
      ) : (
        <div className="mx-auto w-12 h-12 text-blue-500 mb-3 flex items-center justify-center rounded-xl bg-blue-50 border border-blue-100">
          <svg
            className="w-6 h-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
      )}
      <h3 className="text-base font-bold text-slate-900">{title}</h3>
      {description && (
        <p className="mt-1.5 text-sm text-slate-500 max-w-sm mx-auto leading-relaxed">
          {description}
        </p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export interface LoadingStateProps {
  message?: string;
  subMessage?: string;
  className?: string;
}

/**
 * Contextual loading state component.
 */
export function LoadingState({
  message = "Loading...",
  subMessage,
  className = "",
}: LoadingStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center py-16 px-4 text-center ${className}`}
      role="status"
      aria-live="polite"
    >
      <div className="relative mb-4">
        <div className="w-12 h-12 rounded-full border-3 border-blue-100 border-t-blue-600 animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-600" />
        </div>
      </div>
      <p className="text-sm font-semibold text-slate-800 tracking-tight">{message}</p>
      {subMessage && (
        <p className="text-xs text-slate-500 mt-1 max-w-xs">{subMessage}</p>
      )}
    </div>
  );
}

export interface ErrorStateProps {
  title?: string;
  message: string;
  action?: ReactNode;
  className?: string;
}

/**
 * Friendly, constructive error card.
 */
export function ErrorState({
  title = "Something went wrong",
  message,
  action,
  className = "",
}: ErrorStateProps) {
  return (
    <div
      className={`bg-rose-50/70 border border-rose-200/80 rounded-2xl p-5 text-center shadow-2xs ${className}`}
      role="alert"
    >
      <div className="mx-auto w-10 h-10 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mb-3">
        <svg
          className="w-5 h-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h3 className="text-sm font-bold text-rose-900">{title}</h3>
      <p className="mt-1 text-xs text-rose-700 leading-relaxed max-w-md mx-auto">
        {message}
      </p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/**
 * Reusable shimmer skeleton block.
 */
export function SkeletonBlock({
  className = "h-4 w-full rounded-lg",
}: {
  className?: string;
}) {
  return <div className={`skeleton-shimmer ${className}`} />;
}