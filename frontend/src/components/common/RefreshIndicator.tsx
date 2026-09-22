import { ArrowPathIcon } from "@heroicons/react/24/outline";

export interface RefreshIndicatorProps {
  lastUpdated?: string | Date | null;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  isStale?: boolean;
  className?: string;
}

export function RefreshIndicator({
  lastUpdated,
  isRefreshing = false,
  onRefresh,
  isStale = false,
  className = "",
}: RefreshIndicatorProps) {
  const formattedTime = lastUpdated
    ? typeof lastUpdated === "string"
      ? new Date(lastUpdated).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
      : lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : "—";

  return (
    <div className={`flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 ${className}`}>
      <span>
        Updated:{" "}
        <strong className="font-medium text-slate-700 dark:text-slate-300">
          {formattedTime}
        </strong>
        {isStale && <span className="ml-1 text-amber-500 font-semibold">(stale)</span>}
      </span>

      {onRefresh && (
        <button
          type="button"
          onClick={onRefresh}
          disabled={isRefreshing}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Refresh data"
        >
          <ArrowPathIcon
            className={`w-3.5 h-3.5 text-slate-500 dark:text-slate-400 ${
              isRefreshing ? "animate-spin text-indigo-600" : ""
            }`}
          />
          <span>Refresh</span>
        </button>
      )}
    </div>
  );
}

export default RefreshIndicator;
