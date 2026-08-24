import { useQuery } from "@tanstack/react-query";
import {
  BanknotesIcon,
  CheckBadgeIcon,
  NoSymbolIcon,
} from "@heroicons/react/24/outline";

// Recharts imports
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";

// API services
import { getSalaryTiers } from "../api/salary";
import { getDashboardSummary } from "../api/summary";

// UI Components
import Heading from "../components/common/Heading";
import SummaryCard from "../components/common/SummaryCard";
import ChartCard from "../components/common/ChartCard";
import AnalyticsTable from "../components/common/AnalyticsTable";

const PIE_COLORS = [
  "#6366f1", // Indigo
  "#8b5cf6", // Violet
  "#06b6d4", // Cyan
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#ef4444", // Rose
];

// Custom Tooltip component for Recharts
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700/80 p-3 rounded-lg shadow-md text-xs">
        <p className="font-semibold text-slate-800 dark:text-slate-100 mb-1">
          {label}
        </p>
        {payload.map((item: any, idx: number) => (
          <p key={idx} style={{ color: item.color }} className="font-medium">
            {item.name}: {item.value !== null && item.value !== undefined ? item.value.toLocaleString() : "N/A"}
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

  const summaryData = summaryQuery.data?.data;
  const salaryData = salaryQuery.data?.data || [];

  // Derive stats
  const totalBands = salaryData.length;
  const jobsWithSalary = summaryData?.jobs_with_salary || 0;
  const jobsWithoutSalary = summaryData?.jobs_without_salary || 0;

  return (
    <div className="space-y-6">
      <Heading
        title="Salary Distribution"
        subtitle="Earnings brackets, transparency indexes, and job segment densities."
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <SummaryCard
          title="Disclosed Salary Bands"
          value={totalBands}
          description="Monitored income tier ranges"
          icon={BanknotesIcon}
          loading={salaryQuery.isLoading}
        />
        <SummaryCard
          title="Transparency Rate (Disclosed)"
          value={jobsWithSalary.toLocaleString()}
          description="Postings containing starting salary details"
          icon={CheckBadgeIcon}
          loading={summaryQuery.isLoading}
        />
        <SummaryCard
          title="Undisclosed Placements"
          value={jobsWithoutSalary.toLocaleString()}
          description="Advertisements excluding salary details"
          icon={NoSymbolIcon}
          loading={summaryQuery.isLoading}
        />
      </div>

      {/* Pie Chart / Donut visualisation */}
      <ChartCard
        title="Salary Tier Remuneration Segmentation"
        subtitle="Percentage distribution of advertised starting salary bands"
        loading={salaryQuery.isLoading}
        error={salaryQuery.isError}
        empty={salaryData.length === 0}
        onRetry={salaryQuery.refetch}
      >
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={salaryData}
              nameKey="salary_tier"
              dataKey="jobs_count"
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={85}
              paddingAngle={4}
              label={({ name, percent }) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}
              labelLine={false}
            >
              {salaryData.map((_entry: any, index: number) => (
                <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: 10 }} />
          </PieChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Data Inventory Grid */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
          Salary Tier Ranges Breakdown
        </h3>

        <AnalyticsTable
          headers={["Remuneration Salary Band", "Active Advertisements Count", "Percentage of Disclosed Market"]}
          data={salaryData}
          loading={salaryQuery.isLoading}
          error={salaryQuery.isError}
          onRetry={salaryQuery.refetch}
          renderRow={(row, idx) => {
            // Percent of total jobs that HAVE a salary
            const percent = jobsWithSalary > 0 ? ((row.jobs_count / jobsWithSalary) * 100).toFixed(1) : "0";
            return (
              <tr key={idx} className="hover:bg-slate-50/40 dark:hover:bg-slate-850/10">
                <td className="px-6 py-3 font-semibold text-slate-900 dark:text-slate-100">
                  {row.salary_tier}
                </td>
                <td className="px-6 py-3 font-medium">
                  {row.jobs_count.toLocaleString()}
                </td>
                <td className="px-6 py-3">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/20 text-indigo-750 dark:text-indigo-400">
                    {percent}%
                  </span>
                </td>
              </tr>
            );
          }}
        />
      </div>
    </div>
  );
}
export { Salary };
