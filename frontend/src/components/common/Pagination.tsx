import { type ChangeEvent } from "react";
import { ChevronLeftIcon, ChevronRightIcon } from "@heroicons/react/24/outline";
import { PAGE_SIZE_OPTIONS } from "../../constants/pagination";

interface PaginationProps {
  page: number;
  pageSize: number;
  totalPages: number;
  onPageChange: (newPage: number) => void;
  onPageSizeChange?: (newPageSize: number) => void;
  hasPrevious: boolean;
  hasNext: boolean;
}

export default function Pagination({
  page,
  pageSize,
  totalPages,
  onPageChange,
  onPageSizeChange,
  hasPrevious,
  hasNext,
}: PaginationProps) {
  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6 pt-4 border-t border-slate-100 dark:border-slate-800/40">
      
      {onPageSizeChange && (
        <div className="flex items-center space-x-2 text-xs text-slate-500 dark:text-slate-450">
          <span>Show</span>
          <select
            value={pageSize}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => onPageSizeChange(Number(e.target.value))}
            className="px-2.5 py-1 border rounded-lg bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-850 dark:text-slate-200 focus-visible:ring-2 focus-visible:ring-indigo-500 cursor-pointer"
            aria-label="Items size per page"
          >
            {PAGE_SIZE_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
          <span>per page</span>
        </div>
      )}

      <div className="text-xs text-slate-500 dark:text-slate-450">
        Page <span className="font-semibold text-slate-800 dark:text-slate-200">{page}</span> of{" "}
        <span className="font-semibold text-slate-800 dark:text-slate-200">{totalPages || 1}</span>
      </div>

      <div className="flex items-center space-x-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={!hasPrevious}
          className="p-1.5 border border-slate-200 dark:border-slate-805 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-slate-600 dark:text-slate-350 focus-visible:ring-2 focus-visible:ring-indigo-500"
          aria-label="Previous page"
        >
          <ChevronLeftIcon className="w-4 h-4" />
        </button>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={!hasNext}
          className="p-1.5 border border-slate-200 dark:border-slate-805 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-slate-600 dark:text-slate-350 focus-visible:ring-2 focus-visible:ring-indigo-500"
          aria-label="Next page"
        >
          <ChevronRightIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
export { Pagination };
