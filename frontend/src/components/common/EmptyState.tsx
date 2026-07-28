import React from "react";
import { InboxIcon } from "@heroicons/react/24/outline";

interface EmptyStateProps {
  title?: string;
  message?: string;
  icon?: React.ComponentType<{ className?: string }>;
}

export default function EmptyState({
  title = "No data available",
  message = "There are currently no job postings or metrics matching your filter criteria.",
  icon: Icon = InboxIcon,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-slate-50/50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800/40 rounded-xl max-w-md mx-auto my-6">
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 mb-4">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">
        {title}
      </h3>
      <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
        {message}
      </p>
    </div>
  );
}
