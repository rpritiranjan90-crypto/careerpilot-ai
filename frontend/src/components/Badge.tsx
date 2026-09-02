import { ReactNode } from "react";

export interface BadgeProps {
  variant?: "primary" | "success" | "warning" | "error" | "neutral";
  size?: "sm" | "md";
  children: ReactNode;
  className?: string;
  icon?: ReactNode;
}

const variants = {
  primary: "bg-blue-50 text-blue-700 border-blue-200/80",
  success: "bg-emerald-50 text-emerald-700 border-emerald-200/80",
  warning: "bg-amber-50 text-amber-800 border-amber-200/80",
  error: "bg-rose-50 text-rose-700 border-rose-200/80",
  neutral: "bg-slate-50 text-slate-700 border-slate-200/80",
};

const sizes = {
  sm: "px-2 py-0.5 text-xs font-medium rounded-md gap-1",
  md: "px-2.5 py-1 text-xs font-semibold rounded-lg gap-1.5",
};

/**
 * Reusable Badge / Chip component with semantic color coding.
 */
export function Badge({
  variant = "neutral",
  size = "md",
  children,
  className = "",
  icon,
}: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center border
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
    >
      {icon && <span aria-hidden="true">{icon}</span>}
      {children}
    </span>
  );
}
