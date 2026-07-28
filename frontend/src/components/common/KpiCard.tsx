import { type ComponentType } from "react";
import Card from "./Card";
import { SkeletonLine } from "./Loading";

interface KpiCardProps {
  title: string;
  value: string | number | null | undefined;
  description: string;
  icon: ComponentType<{ className?: string }>;
  loading?: boolean;
}

export default function KpiCard({
  title,
  value,
  description,
  icon: Icon,
  loading = false,
}: KpiCardProps) {
  if (loading) {
    return (
      <Card className="animate-pulse">
        <div className="flex items-center justify-between">
          <SkeletonLine className="w-24 h-4" />
          <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800" />
        </div>
        <SkeletonLine className="w-32 h-8 mt-4" />
        <SkeletonLine className="w-40 h-3 mt-3" />
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
    <Card className="hover:scale-[1.01] hover:-translate-y-0.5 active:scale-[1.00] transition-all duration-150 cursor-default">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-450 uppercase tracking-wider">
          {title}
        </span>
        <div className="p-2 bg-indigo-50 dark:bg-indigo-950/20 text-indigo-650 dark:text-indigo-400 rounded-lg">
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline">
        <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white leading-none">
          {displayValue}
        </span>
      </div>

      <p className="mt-2.5 text-xs text-slate-500 dark:text-slate-400 leading-normal truncate" title={description}>
        {description}
      </p>
    </Card>
  );
}
export { KpiCard };
