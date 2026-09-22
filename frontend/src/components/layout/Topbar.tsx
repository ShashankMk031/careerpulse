import { useLocation } from "react-router-dom";
import { Bars3Icon } from "@heroicons/react/24/outline";
import ThemeToggle from "../common/ThemeToggle";
import { useHealth } from "../../hooks/useHealth";

interface TopbarProps {
  onMenuToggle: () => void;
}

const ROUTE_TITLES: Record<string, { section: string; title: string }> = {
  "/dashboard": { section: "Analytics", title: "Executive Dashboard" },
  "/companies": { section: "Market Demand", title: "Hiring Organizations" },
  "/skills": { section: "Market Demand", title: "Skills Intelligence" },
  "/technology": { section: "Market Demand", title: "Technology Stack" },
  "/geography": { section: "Distribution", title: "Geographical Distribution" },
  "/salary": { section: "Compensation", title: "Salary Intelligence" },
  "/status": { section: "Infrastructure", title: "Platform Telemetry" },
  "/about": { section: "Platform", title: "About CareerPulse" },
};

export default function Topbar({ onMenuToggle }: TopbarProps) {
  const location = useLocation();
  const currentRoute = ROUTE_TITLES[location.pathname] || {
    section: "Platform",
    title: "CareerPulse Analytics",
  };

  const { data: healthData, isLoading, isError } = useHealth();

  let statusState: "connected" | "unavailable" | "checking" = "checking";
  let statusLabel = "Checking";
  if (isLoading) {
    statusState = "checking";
    statusLabel = "Checking";
  } else if (isError || !healthData || (healthData as any).status === "error" || (healthData.data && (healthData.data as any).status !== "healthy")) {
    statusState = "unavailable";
    statusLabel = "Unavailable";
  } else {
    statusState = "connected";
    statusLabel = "Connected";
  }

  const statusBadgeClasses = {
    connected:
      "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-800/40",
    unavailable:
      "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:text-red-400 dark:border-red-800/40",
    checking:
      "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800/40",
  }[statusState];

  const dotClasses = {
    connected: "bg-emerald-500",
    unavailable: "bg-red-500",
    checking: "bg-amber-500 animate-pulse",
  }[statusState];

  const envName = import.meta.env.MODE === "production" ? "Production" : "Development";

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 md:px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 transition-colors duration-150">
      {/* Left items: Mobile menu toggle + breadcrumbs */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onMenuToggle}
          type="button"
          className="p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
          aria-label="Open sidebar menu"
        >
          <Bars3Icon className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-2 text-xs">
          <span className="text-slate-400 dark:text-slate-500 font-medium">
            {currentRoute.section}
          </span>
          <span className="text-slate-300 dark:text-slate-600">/</span>
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100 m-0">
            {currentRoute.title}
          </h2>
        </div>
      </div>

      {/* Right items: Environment badge, API status indicator, theme toggle */}
      <div className="flex items-center space-x-3">
        {/* Environment Badge */}
        <span className="hidden sm:inline-flex items-center px-2 py-0.5 text-[10px] font-medium tracking-wide text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md uppercase">
          {envName}
        </span>

        {/* Live API Health Status Indicator */}
        <div
          className={`flex items-center space-x-1.5 px-2.5 py-1 text-xs font-medium border rounded-full transition-colors ${statusBadgeClasses}`}
          title={`API Status: ${statusLabel}`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${dotClasses}`} aria-hidden="true" />
          <span>{statusLabel}</span>
        </div>

        {/* Theme Toggle */}
        <ThemeToggle />
      </div>
    </header>
  );
}

export { Topbar };
