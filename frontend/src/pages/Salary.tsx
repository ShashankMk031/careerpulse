import { useQuery } from "@tanstack/react-query";
import {
  BanknotesIcon,
  CheckBadgeIcon,
  NoSymbolIcon,
  ArrowTrendingUpIcon,
  ArrowPathIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/outline";

// Recharts imports
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

// API services
import { getSalaryTiers } from "../api/salary";
import { getDashboardSummary } from "../api/summary";

// UI Components
import PageHeader from "../components/common/PageHeader";
import StatCard from "../components/common/StatCard";
import ChartCard from "../components/common/ChartCard";
import DataTable, { type ColumnDef } from "../components/common/DataTable";
import Card from "../components/common/Card";

// Formatting
import {
  formatNumber,
  formatCurrency,
  calculatePercentage,
} from "../utils/formatters";
import type { SalaryAnalytics } from "../types/api";

// Custom Tooltip component for Recharts
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-3 rounded-lg shadow-md text-xs">
        <p className="font-semibold text-slate-800 dark:text-slate-100 mb-1">
          {label}
        </p>
        {payload.map((item: any, idx: number) => (
          <p key={idx} style={{ color: item.color }} className="font-medium">
            {item.name}: {item.value !== null && item.value !== undefined ? item.value.toLocaleString() : "N/A"} jobs
            {item.payload?.shareOfDisclosed ? ` (${item.payload.shareOfDisclosed} of disclosed)` : ""}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function Salary() {
  // Queries
  const summaryQuery = useQuery({
    queryKey: ["summary"],
    queryFn: getDashboardSummary,
  });

  const salaryQuery = useQuery({
    queryKey: ["salary_full"],
    queryFn: getSalaryTiers,
  });

  const refetchAll = () => {
    summaryQuery.refetch();
    salaryQuery.refetch();
  };

  const isRefreshing = summaryQuery.isFetching || salaryQuery.isFetching;

  const summaryData = summaryQuery.data?.data;
  const salaryData = salaryQuery.data?.data || [];

  // Summary Metrics derived strictly from /api/v1/salary tiers dataset
  const totalDisclosed = salaryData
    .filter((s) => s.salary_tier !== "Not Specified")
    .reduce((sum, s) => sum + s.jobs_count, 0);

  const undisclosed =
    salaryData.find((s) => s.salary_tier === "Not Specified")?.jobs_count ?? 0;

  const totalJobs =
    salaryData.reduce((sum, s) => sum + s.jobs_count, 0);

  // Macro snapshot metrics explicitly sourced from /api/v1/summary (Current Market Snapshot)
  const medianSalary = summaryData?.median_salary ?? null;
  const highestSalary = summaryData?.highest_salary ?? null;

  // Split into disclosed vs undisclosed
  const disclosedTiers = salaryData.filter((s) => s.salary_tier !== "Not Specified");

  // Chart data: Only disclosed salary tiers with dynamic percentage derivation
  const chartData = disclosedTiers.map((tier) => ({
    ...tier,
    shareOfDisclosed: totalDisclosed > 0 ? calculatePercentage(tier.jobs_count, totalDisclosed) : "—",
  }));

  // Table column definitions
  const columns: ColumnDef<SalaryAnalytics>[] = [
    {
      key: "salary_tier",
      header: "Salary Tier Category",
      render: (item) => {
        const isDisclosed = item.salary_tier !== "Not Specified";
        return (
          <div className="flex items-center space-x-2">
            <span
              className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold ${
                isDisclosed
                  ? "bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 border border-amber-200/60 dark:border-amber-800/40"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700"
              }`}
            >
              {item.salary_tier}
            </span>
          </div>
        );
      },
    },
    {
      key: "tier_type",
      header: "Transparency Status",
      render: (item) => {
        const isDisclosed = item.salary_tier !== "Not Specified";
        return (
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${
              isDisclosed
                ? "bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-400 border border-emerald-100/60 dark:border-emerald-900/30"
                : "bg-slate-50 dark:bg-slate-800/40 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800"
            }`}
          >
            {isDisclosed ? "Disclosed Tier" : "Undisclosed Compensation"}
          </span>
        );
      },
    },
    {
      key: "jobs_count",
      header: "Jobs Count",
      align: "center",
      render: (item) => (
        <span className="font-semibold text-slate-900 dark:text-white">
          {item.jobs_count}
        </span>
      ),
    },
    {
      key: "share_disclosed",
      header: "% of Disclosed Jobs",
      align: "center",
      render: (item) => {
        if (item.salary_tier === "Not Specified") {
          return <span className="text-slate-400 text-xs italic">—</span>;
        }
        return (
          <span className="font-semibold text-amber-700 dark:text-amber-400">
            {totalDisclosed > 0 ? calculatePercentage(item.jobs_count, totalDisclosed) : "—"}
          </span>
        );
      },
    },
    {
      key: "share_total",
      header: "% of Total Market",
      align: "center",
      render: (item) => (
        <span className="text-slate-600 dark:text-slate-300 font-medium">
          {totalJobs > 0 ? calculatePercentage(item.jobs_count, totalJobs) : "—"}
        </span>
      ),
    },
    {
      key: "avg_salary_min",
      header: "Average Min Salary",
      align: "right",
      render: (item) => {
        if (item.avg_salary_min === null || item.avg_salary_min === undefined) {
          return <span className="text-slate-400 text-xs">—</span>;
        }
        return (
          <span className="font-medium text-slate-800 dark:text-slate-200">
            {formatCurrency(item.avg_salary_min)}
          </span>
        );
      },
    },
    {
      key: "avg_salary_max",
      header: "Average Max Salary",
      align: "right",
      render: (item) => {
        if (item.avg_salary_max === null || item.avg_salary_max === undefined) {
          return <span className="text-slate-400 text-xs">—</span>;
        }
        return (
          <span className="font-medium text-slate-800 dark:text-slate-200">
            {formatCurrency(item.avg_salary_max)}
          </span>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Salary Benchmarks"
        subtitle="Compensation tier distribution and salary transparency analytics."
        actions={
          <button
            onClick={refetchAll}
            disabled={isRefreshing}
            className="inline-flex items-center px-3.5 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg shadow-2xs transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Refresh salary data"
          >
            <ArrowPathIcon className={`w-3.5 h-3.5 mr-1.5 ${isRefreshing ? "animate-spin text-indigo-600" : ""}`} />
            Refresh
          </button>
        }
      />

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Jobs With Salary"
          value={salaryQuery.isLoading ? "—" : formatNumber(totalDisclosed)}
          description={`${totalJobs > 0 ? calculatePercentage(totalDisclosed, totalJobs) : "—"} transparency rate (derived from tiers)`}
          icon={CheckBadgeIcon}
          loading={salaryQuery.isLoading}
        />
        <StatCard
          title="Jobs Without Salary"
          value={salaryQuery.isLoading ? "—" : formatNumber(undisclosed)}
          description={`${totalJobs > 0 ? calculatePercentage(undisclosed, totalJobs) : "—"} undisclosed listings (Not Specified)`}
          icon={NoSymbolIcon}
          loading={salaryQuery.isLoading}
        />
        <StatCard
          title="Median Salary"
          value={medianSalary !== null ? formatCurrency(medianSalary) : "—"}
          description="Current market baseline (/api/v1/summary)"
          icon={BanknotesIcon}
          loading={summaryQuery.isLoading}
        />
        <StatCard
          title="Highest Salary"
          value={highestSalary !== null ? formatCurrency(highestSalary) : "—"}
          description="Peak market compensation (/api/v1/summary)"
          icon={ArrowTrendingUpIcon}
          loading={summaryQuery.isLoading}
        />
      </div>

      {/* Disclosed Salary Tiers Bar Chart */}
      <ChartCard
        title="Disclosed Salary Tier Distribution"
        subtitle="Distribution across standard compensation brackets (disclosed listings only)"
        loading={salaryQuery.isLoading}
        error={salaryQuery.isError}
        errorMessage="Failed to load salary tier records."
        empty={chartData.length === 0}
        emptyMessage="No salary tier records available."
        onRetry={salaryQuery.refetch}
      >
        <ResponsiveContainer width="100%" height={280}>
          <BarChart
            layout="vertical"
            data={chartData}
            margin={{ top: 10, right: 30, left: 120, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal vertical={false} stroke="#e2e8f0" className="dark:opacity-15" />
            <XAxis type="number" tick={{ fontSize: 11, fill: "#64748b" }} allowDecimals={false} />
            <YAxis
              dataKey="salary_tier"
              type="category"
              tick={{ fontSize: 11, fill: "#64748b" }}
              width={115}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="jobs_count" name="Jobs Count" fill="#f59e0b" radius={[0, 4, 4, 0]} barSize={20} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Main Salary Tiers DataTable */}
      <DataTable
        columns={columns}
        data={salaryData}
        keyExtractor={(item) => item.salary_tier}
        loading={salaryQuery.isLoading}
        error={salaryQuery.error}
        onRetry={salaryQuery.refetch}
        emptyTitle="No salary tiers found"
        emptyMessage="No salary tier analytics currently recorded."
      />

      {/* Educational Context Card on Compensation Transparency */}
      <Card className="bg-slate-50/70 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800">
        <div className="flex items-start space-x-3">
          <InformationCircleIcon className="w-5 h-5 text-indigo-600 dark:text-indigo-400 mt-0.5 shrink-0" />
          <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            <h2 className="font-semibold text-slate-900 dark:text-white text-sm">
              Understanding Remote Job Market Salary Transparency
            </h2>
            <p>
              In the monitored snapshot of <strong>{totalJobs > 0 ? `${totalJobs} remote positions` : "remote positions"}</strong>, exactly{" "}
              <strong>{totalDisclosed} roles ({totalJobs > 0 ? calculatePercentage(totalDisclosed, totalJobs) : "—"})</strong> disclose verified base salary compensation ranges. The remaining{" "}
              <strong>{undisclosed} postings ({totalJobs > 0 ? calculatePercentage(undisclosed, totalJobs) : "—"})</strong> omit compensation bands entirely, classifying under <em>Not Specified</em>.
            </p>
            <p>
              Disclosed roles demonstrate a strong preference for senior/lead positions, with{" "}
              <strong>Staff ({chartData.find((d) => d.salary_tier.startsWith("Staff"))?.shareOfDisclosed ?? "—"})</strong> commanding the highest volume among disclosed compensation tiers.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
