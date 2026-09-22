interface LoadingStateProps {
  message?: string;
  rows?: number;
  className?: string;
}

export function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div
      className={`p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs animate-pulse ${className}`}
      aria-hidden="true"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="w-24 h-4 bg-slate-200 dark:bg-slate-800 rounded-md" />
        <div className="w-8 h-8 bg-slate-200 dark:bg-slate-800 rounded-lg" />
      </div>
      <div className="w-32 h-7 bg-slate-300 dark:bg-slate-700 rounded-md mb-2" />
      <div className="w-40 h-3 bg-slate-200 dark:bg-slate-800 rounded-md" />
    </div>
  );
}

export function LoadingGrid({ count = 4, columns = 4 }: { count?: number; columns?: number }) {
  const colClass =
    columns === 4
      ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"
      : columns === 3
      ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"
      : "grid-cols-1 sm:grid-cols-2";

  return (
    <div className={`grid ${colClass} gap-5`} aria-busy="true" aria-label="Loading analytics data">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

export default function LoadingState({
  message = "Loading analytics...",
  className = "",
}: LoadingStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-12 text-center ${className}`}
      role="status"
      aria-busy="true"
    >
      <div className="w-9 h-9 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mb-4" />
      <p className="text-sm font-medium text-slate-600 dark:text-slate-400 animate-pulse">{message}</p>
      <span className="sr-only">{message}</span>
    </div>
  );
}
