
export function LoadingSpinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizes = {
    sm: "w-5 h-5 border-2",
    md: "w-8 h-8 border-3",
    lg: "w-12 h-12 border-4",
  };
  return (
    <div className="flex items-center justify-center p-4">
      <div
        className={`${sizes[size]} border-indigo-200 border-t-indigo-600 rounded-full animate-spin`}
        role="status"
        aria-label="loading"
      />
    </div>
  );
}

export function SkeletonLine({ className = "" }: { className?: string }) {
  return (
    <div
      className={`h-4 bg-slate-200 dark:bg-slate-800 rounded animate-pulse ${className}`}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="p-5 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/40 rounded-xl space-y-3">
      <SkeletonLine className="w-1/3 h-5" />
      <SkeletonLine className="w-full h-8" />
      <div className="flex space-x-2 pt-2">
        <SkeletonLine className="w-1/2 h-4" />
        <SkeletonLine className="w-1/4 h-4" />
      </div>
    </div>
  );
}

export function SkeletonList({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center justify-between p-3 border-b border-slate-100 dark:border-slate-800/40">
          <div className="space-y-2 w-2/3">
            <SkeletonLine className="w-1/4 h-4" />
            <SkeletonLine className="w-1/2 h-3" />
          </div>
          <SkeletonLine className="w-16 h-6" />
        </div>
      ))}
    </div>
  );
}

export default function Loading() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[300px] p-6 space-y-4">
      <LoadingSpinner size="lg" />
      <p className="text-sm font-medium text-slate-500 dark:text-slate-450 animate-pulse">
        Loading view dashboard...
      </p>
    </div>
  );
}
