import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  CpuChipIcon,
  SparklesIcon,
  BuildingOfficeIcon,
  ArrowTrendingUpIcon,
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
import { getTechnology } from "../api/technology";

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
import type { TechnologyAnalytics } from "../types/api";

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

export default function Technology() {
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
  const chartTechQuery = useQuery({
    queryKey: ["tech_chart"],
    queryFn: () =>
      getTechnology({
        page_size: 10,
        sort_by: "job_demand_count",
        sort_order: "desc",
      }),
  });

  const tableQuery = useQuery({
    queryKey: ["tech_table", { search, sortBy, sortOrder, page, pageSize }],
    queryFn: () =>
      getTechnology({
        search,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: pageSize,
      }),
  });

  const refetchAll = () => {
    chartTechQuery.refetch();
    tableQuery.refetch();
  };

  const isRefreshing = chartTechQuery.isFetching || tableQuery.isFetching;

  const chartData = chartTechQuery.data?.data || [];
  const tableEnvelope = tableQuery.data;
  const tableData = tableEnvelope?.data || [];
  const metadata = tableEnvelope?.metadata;

  // Derive stats
  const uniqueTech = metadata?.total_records ?? null;
  const topTechItem = chartData.length > 0 ? chartData[0] : null;
  const highestDemand = topTechItem ? `${topTechItem.job_demand_count} jobs` : "—";
  const topTechName = topTechItem ? topTechItem.tech_tag : "—";
  const maxDemandForBar = topTechItem ? topTechItem.job_demand_count : 1;

  const avgDemand =
    chartData.length > 0
      ? (chartData.reduce((acc, curr) => acc + curr.job_demand_count, 0) / chartData.length).toFixed(1)
      : "—";

  // Table column definitions
  const columns: ColumnDef<TechnologyAnalytics>[] = [
    {
      key: "rank",
      header: "#",
      align: "center",
      className: "w-12 text-slate-400 font-mono text-xs",
      render: (_, idx) => <span>{(page - 1) * pageSize + idx + 1}</span>,
    },
    {
      key: "tech_tag",
      header: "Technology",
      render: (item) => (
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-cyan-50 dark:bg-cyan-950/30 text-cyan-700 dark:text-cyan-300 border border-cyan-200/50 dark:border-cyan-800/40">
            <CpuChipIcon className="w-3.5 h-3.5 mr-1 text-cyan-500" />
            {item.tech_tag}
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
              <span className="text-[11px] text-slate-400" title="Relative Demand (% of peak technology)">
                {pct}% of peak
              </span>
            </div>
            <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden" title={`Relative demand: ${pct}% of peak technology`}>
              <div
                className="bg-cyan-500 h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      },
    },
    {
      key: "top_company",
      header: "Top Hiring Employer",
      render: (item) => {
        if (!item.top_company) return <span className="text-slate-400 text-xs">—</span>;
        return (
          <div className="inline-flex items-center space-x-1.5 text-slate-700 dark:text-slate-300">
            <BuildingOfficeIcon className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-medium">{item.top_company}</span>
          </div>
        );
      },
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
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Technology & Tooling"
        subtitle="Technical tooling demand and associated hiring companies."
        actions={
          <button
            onClick={refetchAll}
            disabled={isRefreshing}
            className="inline-flex items-center px-3.5 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg shadow-2xs transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Refresh technology data"
          >
            <ArrowPathIcon className={`w-3.5 h-3.5 mr-1.5 ${isRefreshing ? "animate-spin text-indigo-600" : ""}`} />
            Refresh
          </button>
        }
      />

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Unique Technologies"
          value={uniqueTech !== null ? formatNumber(uniqueTech) : "—"}
          description="Tracked tools & technical tags"
          icon={CpuChipIcon}
          loading={tableQuery.isLoading}
        />
        <StatCard
          title="Highest Demand"
          value={highestDemand}
          description={topTechItem ? `Peak postings for #${topTechName}` : "Peak postings among technologies"}
          icon={SparklesIcon}
          loading={chartTechQuery.isLoading}
        />
        <StatCard
          title="Most Requested Technology"
          value={topTechName}
          description="Leader by active job mentions"
          icon={ArrowTrendingUpIcon}
          loading={chartTechQuery.isLoading}
        />
        <StatCard
          title="Average Demand"
          value={avgDemand !== "—" ? `${avgDemand} jobs` : "—"}
          description="Mean demand across top tooling"
          icon={CpuChipIcon}
          loading={chartTechQuery.isLoading}
        />
      </div>

      {/* Top 10 Technology Bar Chart */}
      <ChartCard
        title="Top 10 Technology Demand"
        subtitle="Hiring demand volume across programming languages, frameworks, and platforms"
        loading={chartTechQuery.isLoading}
        error={chartTechQuery.isError}
        errorMessage="Failed to load technology chart records."
        empty={chartData.length === 0}
        emptyMessage="No technology demand records available."
        onRetry={chartTechQuery.refetch}
      >
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            layout="vertical"
            data={chartData.slice(0, 10).map((d) => ({
              ...d,
              truncatedTag: truncateText(d.tech_tag, 20),
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
            <Bar dataKey="job_demand_count" name="Demand Count" fill="#06b6d4" radius={[0, 4, 4, 0]} barSize={16} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Filter and Search Bar */}
      <FilterBar>
        <SearchBox
          value={search}
          onChange={(val) => updateParams({ search: val })}
          placeholder="Search technology by tag..."
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
            <option value="tech_tag">Technology Name</option>
            <option value="top_company">Top Employer</option>
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

      {/* Main Technology DataTable */}
      <DataTable
        columns={columns}
        data={tableData}
        keyExtractor={(item) => item.tech_tag}
        loading={tableQuery.isLoading}
        error={tableQuery.error}
        onRetry={tableQuery.refetch}
        emptyTitle="No technologies found"
        emptyMessage={
          search
            ? `No technologies matching "${search}" were found in the dataset.`
            : "No technology records currently recorded."
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
