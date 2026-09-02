import { ReactNode } from "react";

export interface CardProps {
  title?: string;
  description?: string;
  children: ReactNode;
  className?: string;
  action?: ReactNode;
  badge?: ReactNode;
  headerClassName?: string;
}

/**
 * Modern, accessible SaaS Card component with refined borders and elevation.
 */
export function Card({
  title,
  description,
  children,
  className = "",
  action,
  badge,
  headerClassName = "",
}: CardProps) {
  return (
    <section
      className={`bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs hover:border-slate-300/80 transition-colors ${className}`}
    >
      {(title || action || badge) && (
        <header
          className={`flex items-start justify-between gap-4 mb-5 ${headerClassName}`}
        >
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              {title && (
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                  {title}
                </h2>
              )}
              {badge}
            </div>
            {description && (
              <p className="text-sm text-slate-500 leading-relaxed">
                {description}
              </p>
            )}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </header>
      )}
      <div>{children}</div>
    </section>
  );
}