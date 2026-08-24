import { type ReactNode } from "react";

interface FilterBarProps {
  children: ReactNode;
}

export default function FilterBar({ children }: FilterBarProps) {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 mb-6 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/40 rounded-xl shadow-2xs transition-colors">
      {children}
    </div>
  );
}
export { FilterBar };
