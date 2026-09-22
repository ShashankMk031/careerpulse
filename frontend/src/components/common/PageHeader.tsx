import { type ReactNode } from "react";

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children?: ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  subtitle,
  actions,
  children,
  className = "",
}: PageHeaderProps) {
  return (
    <div
      className={`flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800 ${className}`}
    >
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {subtitle}
          </p>
        )}
      </div>
      {(actions || children) && (
        <div className="flex flex-wrap items-center gap-3">
          {actions}
          {children}
        </div>
      )}
    </div>
  );
}

export default PageHeader;
