import { type ReactNode } from "react";

export type BadgeStatus = "success" | "warning" | "error" | "neutral";

interface StatusBadgeProps {
  status: BadgeStatus;
  children: ReactNode;
}

export default function StatusBadge({ status, children }: StatusBadgeProps) {
  const styles = {
    success: "bg-emerald-50 text-emerald-700 border-emerald-100/50 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/30",
    warning: "bg-amber-50 text-amber-755 border-amber-100/50 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900/30",
    error: "bg-red-50 text-red-700 border-red-100/50 dark:bg-red-950/20 dark:text-red-400 dark:border-red-900/30",
    neutral: "bg-slate-50 text-slate-700 border-slate-105/50 dark:bg-slate-900/40 dark:text-slate-400 dark:border-slate-800/30",
  };

  const dots = {
    success: "bg-emerald-500",
    warning: "bg-amber-500",
    error: "bg-red-500",
    neutral: "bg-slate-400",
  };

  return (
    <span className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 border rounded-full text-xs font-medium transition-colors ${styles[status]}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dots[status]}`} />
      <span>{children}</span>
    </span>
  );
}
