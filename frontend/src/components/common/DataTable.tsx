import { type ReactNode } from "react";
import { SkeletonList } from "./Loading";
import EmptyState from "./EmptyState";
import ErrorState from "./ErrorState";
import Pagination from "./Pagination";

export interface ColumnDef<T> {
  key: string;
  header: string;
  align?: "left" | "center" | "right";
  className?: string;
  render?: (item: T, index: number) => ReactNode;
}

export interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  keyExtractor?: (item: T, index: number) => string | number;
  loading?: boolean;
  error?: string | Error | null;
  onRetry?: () => void;
  emptyMessage?: string;
  emptyTitle?: string;
  pagination?: {
    currentPage: number;
    pageSize?: number;
    totalPages: number;
    onPageChange: (page: number) => void;
    onPageSizeChange?: (pageSize: number) => void;
    hasNext?: boolean;
    hasPrevious?: boolean;
    totalRecords?: number;
  };
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  loading = false,
  error = null,
  onRetry,
  emptyTitle,
  emptyMessage,
  pagination,
  className = "",
}: DataTableProps<T>) {
  if (loading) {
    return (
      <div className={`border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden bg-white dark:bg-slate-900 ${className}`}>
        <SkeletonList rows={5} />
      </div>
    );
  }

  if (error) {
    const errorMsg = typeof error === "string" ? error : error?.message || "Failed to load table records.";
    return (
      <div className={`border border-slate-200 dark:border-slate-800 rounded-xl p-8 bg-white dark:bg-slate-900 flex justify-center ${className}`}>
        <ErrorState message={errorMsg} onRetry={onRetry} />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className={`border border-slate-200 dark:border-slate-800 rounded-xl p-8 bg-white dark:bg-slate-900 flex justify-center ${className}`}>
        <EmptyState title={emptyTitle} message={emptyMessage} />
      </div>
    );
  }

  const getAlignmentClass = (align?: "left" | "center" | "right") => {
    if (align === "right") return "text-right";
    if (align === "center") return "text-center";
    return "text-left";
  };

  return (
    <div className={`border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden bg-white dark:bg-slate-900 shadow-xs flex flex-col ${className}`}>
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850 text-slate-500 dark:text-slate-400 uppercase font-semibold tracking-wider">
              {columns.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  className={`px-6 py-3.5 ${getAlignmentClass(col.align)} ${col.className || ""}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
            {data.map((item, idx) => {
              const rowKey = keyExtractor ? keyExtractor(item, idx) : (item as any)?.id ?? idx;
              return (
                <tr
                  key={rowKey}
                  className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                >
                  {columns.map((col) => {
                    const content = col.render
                      ? col.render(item, idx)
                      : (item as any)[col.key] !== undefined && (item as any)[col.key] !== null
                      ? String((item as any)[col.key])
                      : "—";

                    return (
                      <td
                        key={col.key}
                        className={`px-6 py-3.5 whitespace-nowrap ${getAlignmentClass(col.align)} ${col.className || ""}`}
                      >
                        {content}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {pagination && pagination.totalPages > 1 && (
        <div className="border-t border-slate-200 dark:border-slate-800 px-6 py-3 bg-slate-50/50 dark:bg-slate-900/50 flex items-center justify-between">
          {pagination.totalRecords !== undefined && (
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Showing page {pagination.currentPage} of {pagination.totalPages} ({pagination.totalRecords.toLocaleString()} total records)
            </span>
          )}
          <Pagination
            page={pagination.currentPage}
            pageSize={pagination.pageSize ?? 10}
            totalPages={pagination.totalPages}
            onPageChange={pagination.onPageChange}
            onPageSizeChange={pagination.onPageSizeChange}
            hasNext={pagination.hasNext ?? pagination.currentPage < pagination.totalPages}
            hasPrevious={pagination.hasPrevious ?? pagination.currentPage > 1}
          />
        </div>
      )}
    </div>
  );
}

export default DataTable;
