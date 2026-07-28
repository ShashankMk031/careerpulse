import { type ReactNode } from "react";

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export default function SectionHeader({
  title,
  subtitle,
  actions,
}: SectionHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 dark:border-slate-850/30 pb-3 mb-5 gap-2">
      <div>
        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 my-0 leading-tight">
          {title}
        </h2>
        {subtitle && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-0 leading-normal">
            {subtitle}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
export { SectionHeader };
