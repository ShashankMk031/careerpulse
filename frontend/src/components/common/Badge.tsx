import { type ReactNode } from "react";

export type BadgeVariant = "success" | "warning" | "error" | "info" | "neutral";

export interface BadgeProps {
  variant?: BadgeVariant;
  size?: "sm" | "md";
  showDot?: boolean;
  children: ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  success:
    "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-800/40",
  warning:
    "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800/40",
  error:
    "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:text-red-400 dark:border-red-800/40",
  info:
    "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/30 dark:text-sky-400 dark:border-sky-800/40",
  neutral:
    "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
};

const dotColors: Record<BadgeVariant, string> = {
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  error: "bg-red-500",
  info: "bg-sky-500",
  neutral: "bg-slate-400",
};

export function Badge({
  variant = "neutral",
  size = "md",
  showDot = true,
  children,
  className = "",
}: BadgeProps) {
  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs";

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border transition-colors ${sizeClasses} ${variantStyles[variant]} ${className}`}
    >
      {showDot && (
        <span
          className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColors[variant]}`}
          aria-hidden="true"
        />
      )}
      <span>{children}</span>
    </span>
  );
}

export default Badge;
