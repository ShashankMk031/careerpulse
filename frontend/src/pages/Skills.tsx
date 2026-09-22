import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  SparklesIcon,
  TagIcon,
  ArrowTrendingUpIcon,
  GlobeAltIcon,
  ArrowPathIcon,
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
import { getSkills } from "../api/skills";

// UI Components
import PageHeader from "../components/common/PageHeader";
import StatCard from "../components/common/StatCard";
import ChartCard from "../components/common/ChartCard";
import DataTable, { type ColumnDef } from "../components/common/DataTable";
import SearchBox from "../components/common/SearchBox";
import FilterBar from "../components/common/FilterBar";

// Formatting
import {
  formatNumber,
  formatCurrency,
  truncateText,
} from "../utils/formatters";
import type { SkillAnalytics } from "../types/api";

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
            {item.name}: {item.value !== null && item.value !== undefined ? item.value.toLocaleString() : "N/A"}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function Skills() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Extract parameters from URL
  const search = searchParams.get("search") || "";
  const sortBy = searchParams.get("sort_by") || "job_demand_count";
  const sortOrder = searchParams.get("sort_order") || "desc";
  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = parseInt(searchParams.get("page_size") || "10", 10);

  // Update URL state helpers
  const updateParams = (newParams: Record<string, any>) => {
    const updated = new URLSearchParams(searchParams);
    Object.entries(newParams).forEach(([key, val]) => {
      if (val === undefined || val === null || val === "") {
        updated.delete(key);
      } else {
        updated.set(key, String(val));
      }
    });
    if (!newParams.page && (newParams.search !== undefined || newParams.sort_by !== undefined || newParams.page_size !== undefined)) {
      updated.set("page", "1");
    }
    setSearchParams(updated);
  };

  // Queries
  const chartSkillsQuery = useQuery({
    queryKey: ["skills_chart"],
    queryFn: () =>
      getSkills({
        page_size: 10,
        sort_by: "job_demand_count",
        sort_order: "desc",
      }),
  });

  const tableQuery = useQuery({
    queryKey: ["skills_table", { search, sortBy, sortOrder, page, pageSize }],
    queryFn: () =>
      getSkills({
        search,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: pageSize,
      }),
  });

  const refetchAll = () => {
    chartSkillsQuery.refetch();
    tableQuery.refetch();
  };

  const isRefreshing = chartSkillsQuery.isFetching || tableQuery.isFetching;

  const chartData = chartSkillsQuery.data?.data || [];
  const tableEnvelope = tableQuery.data;
  const tableData = tableEnvelope?.data || [];
  const metadata = tableEnvelope?.metadata;

  // Derive stats strictly from skills endpoint
  const uniqueSkills = metadata?.total_records ?? null;
  const topSkillItem = chartData.length > 0 ? chartData[0] : null;
  const highestDemand = topSkillItem ? `${topSkillItem.job_demand_count} jobs` : "—";
  const topSkillName = topSkillItem ? `#${topSkillItem.tag}` : "—";
  const maxDemandForBar = topSkillItem ? topSkillItem.job_demand_count : 1;

  // Average demand calculation from chart records
  const avgDemand =
    chartData.length > 0
      ? (chartData.reduce((acc, curr) => acc + curr.job_demand_count, 0) / chartData.length).toFixed(1)
      : "—";

  // Table column definitions
  const columns: ColumnDef<SkillAnalytics>[] = [
    {
      key: "rank",
      header: "#",
      align: "center",
      className: "w-12 text-slate-400 font-mono text-xs",
      render: (_, idx) => <span>{(page - 1) * pageSize + idx + 1}</span>,
    },
    {
      key: "tag",
      header: "Skill Tag",
      render: (item) => (
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-violet-50 dark:bg-violet-950/30 text-violet-700 dark:text-violet-300 border border-violet-200/50 dark:border-violet-800/40">
            <TagIcon className="w-3 h-3 mr-1 text-violet-500" />
            {item.tag}
          </span>
        </div>
      ),
    },
    {
      key: "job_demand_count",
      header: "Demand Count",
      render: (item) => {
        const pct = Math.min(100, Math.round((item.job_demand_count / maxDemandForBar) * 100));
        return (
          <div className="w-48">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-slate-900 dark:text-white">
                {item.job_demand_count} jobs
              </span>
              <span className="text-[11px] text-slate-400" title="Relative Demand (% of peak skill)">
                {pct}% of peak
              </span>
            </div>
            <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden" title={`Relative demand: ${pct}% of peak skill`}>
              <div
                className="bg-violet-500 h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      },
    },
    {
      key: "remote_jobs_count",
      header: "Remote Listings",
      align: "center",
      render: (item) => (
        <div className="inline-flex items-center space-x-1 text-slate-600 dark:text-slate-300">
          <GlobeAltIcon className="w-3.5 h-3.5 text-slate-400" />
          <span>{item.remote_jobs_count}</span>
        </div>
      ),
    },
    {
      key: "salary_range",
      header: "Salary Range",
      render: (item) => {
        if (item.avg_salary_min !== null && item.avg_salary_max !== null) {
          return (
            <span className="font-medium text-emerald-700 dark:text-emerald-400">
              {formatCurrency(item.avg_salary_min, true)} – {formatCurrency(item.avg_salary_max, true)}
            </span>
          );
        }
        return <span className="text-slate-400 dark:text-slate-500 italic text-xs">Undisclosed</span>;
      },
    },
    {
      key: "salary_premium",
      header: "Salary Premium",
      align: "right",
      render: (item) => {
        if (item.salary_premium === null || item.salary_premium === undefined) {
          return <span className="text-slate-400 text-xs">—</span>;
        }
        const isPositive = item.salary_premium >= 0;
        return (
          <span
            className={`font-semibold text-xs ${
              isPositive
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-slate-500 dark:text-slate-400"
            }`}
          >
            {isPositive ? "+" : ""}
            {formatCurrency(item.salary_premium, true)}
          </span>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Skills Demand"
        subtitle="Analysis of in-demand technical competencies and market frequencies."
        actions={
          <button
            onClick={refetchAll}
            disabled={isRefreshing}
            className="inline-flex items-center px-3.5 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg shadow-2xs transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Refresh skill data"
          >
            <ArrowPathIcon className={`w-3.5 h-3.5 mr-1.5 ${isRefreshing ? "animate-spin text-indigo-600" : ""}`} />
            Refresh
          </button>
        }
      />

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Unique Skills"
          value={uniqueSkills !== null ? formatNumber(uniqueSkills) : "—"}
          description="Monitored skill tags across dataset"
          icon={TagIcon}
          loading={tableQuery.isLoading}
        />
        <StatCard
          title="Highest Demand"
          value={highestDemand}
          description={topSkillItem ? `Peak frequency for ${topSkillName}` : "Peak frequency among skills"}
          icon={SparklesIcon}
          loading={chartSkillsQuery.isLoading}
        />
        <StatCard
          title="Top Skill"
          value={topSkillName}
          description="Most requested market capability"
          icon={ArrowTrendingUpIcon}
          loading={chartSkillsQuery.isLoading}
        />
        <StatCard
          title="Average Demand"
          value={avgDemand !== "—" ? `${avgDemand} jobs` : "—"}
          description="Mean demand across top skills"
          icon={TagIcon}
          loading={chartSkillsQuery.isLoading}
        />
      </div>

      {/* Top 10 Skills Horizontal Bar Chart */}
      <ChartCard
        title="Top 10 In-Demand Skills"
        subtitle="Frequency of requested capabilities across open positions"
        loading={chartSkillsQuery.isLoading}
        error={chartSkillsQuery.isError}
        errorMessage="Failed to load skills chart records."
        empty={chartData.length === 0}
        emptyMessage="No skill demand records available."
        onRetry={chartSkillsQuery.refetch}
      >
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            layout="vertical"
            data={chartData.slice(0, 10).map((d) => ({
              ...d,
              truncatedTag: truncateText(d.tag, 20),
            }))}
            margin={{ top: 10, right: 30, left: 110, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal vertical={false} stroke="#e2e8f0" className="dark:opacity-15" />
            <XAxis type="number" tick={{ fontSize: 11, fill: "#64748b" }} allowDecimals={false} />
            <YAxis
              dataKey="truncatedTag"
              type="category"
              tick={{ fontSize: 11, fill: "#64748b" }}
              width={105}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="job_demand_count" name="Demand Count" fill="#8b5cf6" radius={[0, 4, 4, 0]} barSize={16} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Filter and Search Bar */}
      <FilterBar>
        <SearchBox
          value={search}
          onChange={(val) => updateParams({ search: val })}
          placeholder="Search skills by tag..."
        />

        <div className="flex flex-wrap items-center gap-3">
          <label htmlFor="sort-select" className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Sort
          </label>
          <select
            id="sort-select"
            value={sortBy}
            onChange={(e) => updateParams({ sort_by: e.target.value })}
            className="px-3 py-1.5 border rounded-lg text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 cursor-pointer focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            <option value="job_demand_count">Job Demand</option>
            <option value="tag">Skill Name</option>
            <option value="remote_jobs_count">Remote Count</option>
            <option value="salary_premium">Salary Premium</option>
          </select>

          <select
            aria-label="Sort order"
            value={sortOrder}
            onChange={(e) => updateParams({ sort_order: e.target.value })}
            className="px-3 py-1.5 border rounded-lg text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 cursor-pointer focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </FilterBar>

      {/* Main Skills DataTable */}
      <DataTable
        columns={columns}
        data={tableData}
        keyExtractor={(item) => item.tag}
        loading={tableQuery.isLoading}
        error={tableQuery.error}
        onRetry={tableQuery.refetch}
        emptyTitle="No skills found"
        emptyMessage={
          search
            ? `No skills matching "${search}" were found in the dataset.`
            : "No skill records currently recorded."
        }
        pagination={
          metadata
            ? {
                currentPage: metadata.page,
                pageSize: metadata.page_size,
                totalPages: metadata.total_pages,
                totalRecords: metadata.total_records,
                hasNext: metadata.has_next,
                hasPrevious: metadata.has_previous,
                onPageChange: (newPage) => updateParams({ page: newPage }),
                onPageSizeChange: (newPageSize) => updateParams({ page_size: newPageSize, page: 1 }),
              }
            : undefined
        }
      />
    </div>
  );
}
