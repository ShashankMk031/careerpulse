import { Bars3Icon } from "@heroicons/react/24/outline";
import ThemeToggle from "../common/ThemeToggle";

interface TopbarProps {
  onMenuToggle: () => void;
}

export default function Topbar({ onMenuToggle }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 md:px-6 bg-white dark:bg-slate-900 border-b border-slate-100 dark:border-slate-800/40 shadow-xs transition-colors duration-150">
      
      {/* Left items: Menu button & Title */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onMenuToggle}
          type="button"
          className="p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800/85 lg:hidden focus:outline-none focus:ring-2 focus:ring-indigo-500"
          aria-label="Open sidebar menu"
        >
          <Bars3Icon className="w-6 h-6" />
        </button>

        <div className="hidden sm:block">
          <span className="text-xs font-semibold text-indigo-650 dark:text-indigo-400 uppercase tracking-wider block leading-none mb-1">
            Platform Serve
          </span>
          <h2 className="text-base font-bold text-slate-800 dark:text-white leading-none my-0">
            CareerPulse Analytics
          </h2>
        </div>
      </div>

      {/* Right items: API status & Theme toggle */}
      <div className="flex items-center space-x-4">
        {/* Status Indicator */}
        <div className="flex items-center space-x-2 px-3 py-1 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-400 border border-emerald-100/50 dark:border-emerald-950/20 rounded-full text-xs font-medium">
          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
          <span>API Connected</span>
        </div>

        {/* Theme toggle */}
        <ThemeToggle />
      </div>
    </header>
  );
}
