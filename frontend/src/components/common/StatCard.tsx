import { type ComponentType } from "react";
import Card from "./Card";
import { SkeletonLine } from "./Loading";

export interface StatCardProps {
  title: string;
  value: string | number | null | undefined;
  description?: string;
  icon?: ComponentType<{ className?: string }>;
  loading?: boolean;
  change?: {
    value: string | number;
    isPositive?: boolean;
  };
  className?: string;
}

export function StatCard({
  title,
  value,
  description,
  icon: Icon,
  loading = false,
  change,
  className = "",
}: StatCardProps) {
  if (loading) {
    return (
      <Card className={`animate-pulse ${className}`}>
        <div className="flex items-center justify-between">
          <SkeletonLine className="w-24 h-4" />
          {Icon && <div className="w-8 h-8 rounded-lg bg-slate-200 dark:bg-slate-800" />}
        </div>
        <SkeletonLine className="w-32 h-8 mt-4" />
        {description && <SkeletonLine className="w-40 h-3 mt-3" />}
      </Card>
    );
  }

  const displayValue =
    value !== null && value !== undefined
      ? typeof value === "number"
        ? value.toLocaleString()
        : value
      : "—";

  return (
    <Card className={`hover:border-slate-300 dark:hover:border-slate-700 transition-colors duration-150 ${className}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          {title}
        </span>
        {Icon && (
          <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400">
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white leading-none">
          {displayValue}
        </span>
        {change && (
          <span
            className={`text-xs font-semibold ${
              change.isPositive
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            {change.isPositive ? "+" : ""}
            {change.value}
          </span>
        )}
      </div>

      {description && (
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400 truncate" title={description}>
          {description}
        </p>
      )}
    </Card>
  );
}

export default StatCard;
