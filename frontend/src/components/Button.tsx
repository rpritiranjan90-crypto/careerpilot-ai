import { ButtonHTMLAttributes, ReactNode } from "react";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  children: ReactNode;
}

const variants = {
  primary:
    "bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 shadow-xs focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:bg-blue-400 border border-transparent",
  secondary:
    "bg-white text-slate-700 hover:bg-slate-50 active:bg-slate-100 border border-slate-200 shadow-2xs focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2 disabled:bg-slate-50 disabled:text-slate-400",
  ghost:
    "bg-transparent text-slate-600 hover:bg-slate-100/80 hover:text-slate-900 active:bg-slate-200 focus-visible:ring-2 focus-visible:ring-slate-400 disabled:text-slate-300",
  danger:
    "bg-red-600 text-white hover:bg-red-700 active:bg-red-800 shadow-xs focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 disabled:bg-red-400 border border-transparent",
};

const sizes = {
  sm: "px-3 py-1.5 text-xs font-semibold rounded-lg min-h-[36px]",
  md: "px-4 py-2 text-sm font-semibold rounded-xl min-h-[42px]",
  lg: "px-6 py-2.5 text-base font-semibold rounded-xl min-h-[48px]",
};

/**
 * Accessible, modern SaaS button component with loading state and micro-interactions.
 */
export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  children,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={`
        inline-flex items-center justify-center gap-2
        transition-all duration-150 ease-out
        active:scale-[0.98]
        focus:outline-none
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
      aria-busy={loading}
    >
      {loading && (
        <svg
          className="animate-spin w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}