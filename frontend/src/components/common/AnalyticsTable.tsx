import { type ReactNode } from "react";
import { SkeletonList } from "./Loading";
import EmptyState from "./EmptyState";
import ErrorState from "./ErrorState";

interface AnalyticsTableProps<T> {
  headers: string[];
  data: T[];
  loading: boolean;
  error?: boolean;
  errorMessage?: string;
  onRetry?: () => void;
  renderRow: (row: T, idx: number) => ReactNode;
}

export default function AnalyticsTable({
  headers,
  data,
  loading,
  error = false,
  errorMessage,
  onRetry,
  renderRow,
}: AnalyticsTableProps<any>) {
  if (loading) {
    return (
      <div className="border border-slate-100 dark:border-slate-800/40 rounded-xl overflow-hidden bg-white dark:bg-slate-900">
        <SkeletonList rows={5} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-slate-100 dark:border-slate-800/40 rounded-xl p-8 bg-white dark:bg-slate-900 flex justify-center">
        <ErrorState message={errorMessage} onRetry={onRetry} />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="border border-slate-100 dark:border-slate-800/40 rounded-xl p-8 bg-white dark:bg-slate-900 flex justify-center">
        <EmptyState />
      </div>
    );
  }

  return (
    <div className="border border-slate-100 dark:border-slate-800/40 rounded-xl overflow-hidden bg-white dark:bg-slate-900 shadow-2xs">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-105 dark:border-slate-800/50 bg-slate-50/50 dark:bg-slate-900/50 text-slate-450 uppercase font-semibold">
              {headers.map((h, i) => (
                <th key={i} className="px-6 py-3.5 font-semibold">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50 dark:divide-slate-800/30 text-slate-700 dark:text-slate-300">
            {data.map((row, idx) => renderRow(row, idx))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
export { AnalyticsTable };
