import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  CpuChipIcon,
  SparklesIcon,
  ChartBarIcon,
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
import Heading from "../components/common/Heading";
import FilterBar from "../components/common/FilterBar";
import SearchBox from "../components/common/SearchBox";
import SummaryCard from "../components/common/SummaryCard";
import ChartCard from "../components/common/ChartCard";
import AnalyticsTable from "../components/common/AnalyticsTable";
import Pagination from "../components/common/Pagination";

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

export default function Technology() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Extract parameters from URL
  const search = searchParams.get("search") || "";
  const sortBy = searchParams.get("sort_by") || "job_demand_count";
  const sortOrder = searchParams.get("sort_order") || "desc";
  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = parseInt(searchParams.get("page_size") || "20", 10);

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
    if (!newParams.page && newParams.search !== undefined) {
      updated.set("page", "1");
    }
    setSearchParams(updated);
  };

  // Queries
  const chartTechQuery = useQuery({
    queryKey: ["tech_chart"],
    queryFn: () =>
      getTechnology({
        page_size: 15,
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

  const chartData = chartTechQuery.data?.data || [];
  const tableEnvelope = tableQuery.data;
  const tableData = tableEnvelope?.data || [];
  const metadata = tableEnvelope?.metadata;

  // Derive stats
  const uniqueTech = metadata?.total_records || 0;
  
  // Find top technology dynamically from sorted chart results
  const topTech = chartData.length > 0 ? chartData[0].tech_tag : "—";

  // Calculate average demand dynamically from current table
  const avgDemand =
    tableData.length > 0
      ? (
          tableData.reduce((acc, curr) => acc + curr.job_demand_count, 0) /
          tableData.length
        ).toFixed(1)
      : "—";

  return (
    <div className="space-y-6">
      <Heading
        title="Technology Analytics"
        subtitle="Developer stack requirements, database technologies, and framework adoption metrics."
      />

      {/* Filter toolbar bar */}
      <FilterBar>
        <SearchBox
          value={search}
          onChange={(val) => updateParams({ search: val })}
          placeholder="Search technology..."
        />

        {/* Ordering Controls */}
        <div className="flex items-center space-x-3">
          <label htmlFor="sort-select" className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Sort
          </label>
          <select
            id="sort-select"
            value={sortBy}
            onChange={(e) => updateParams({ sort_by: e.target.value })}
            className="px-3 py-1.5 border rounded-lg text-sm bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 cursor-pointer focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            <option value="job_demand_count">Demand</option>
            <option value="tech_tag">Alphabetical</option>
          </select>
          <select
            aria-label="Sort order"
            value={sortOrder}
            onChange={(e) => updateParams({ sort_order: e.target.value })}
            className="px-3 py-1.5 border rounded-lg text-sm bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 cursor-pointer focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </FilterBar>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <SummaryCard
          title="Technologies Tracked"
          value={uniqueTech}
          description="Different technologies monitored"
          icon={CpuChipIcon}
          loading={tableQuery.isLoading}
        />
        <SummaryCard
          title="Most Demanded Technology"
          value={topTech}
          description="Highest appearing technology tag"
          icon={SparklesIcon}
          loading={chartTechQuery.isLoading}
        />
        <SummaryCard
          title="Average Demand Count"
          value={avgDemand}
          description="Average appearances per tag"
          icon={ChartBarIcon}
          loading={tableQuery.isLoading}
        />
      </div>

      {/* Technology Demand Horizontal Bar Chart */}
      <ChartCard
        title="Technology Demand Breakdown"
        subtitle="Engineering framework and tooling volumes"
        loading={chartTechQuery.isLoading}
        error={chartTechQuery.isError}
        empty={chartData.length === 0}
        onRetry={chartTechQuery.refetch}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={chartData.slice(0, 15)}
            margin={{ left: 100, right: 10, top: 10, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#334155" opacity={0.1} />
            <XAxis type="number" stroke="#64748b" fontSize={10} tickLine={false} />
            <YAxis
              dataKey="tech_tag"
              type="category"
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              width={90}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(100, 116, 139, 0.05)" }} />
            <Bar dataKey="job_demand_count" fill="#06b6d4" radius={[0, 4, 4, 0]} name="Demand Count" />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Paginated Data Grid */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
          All Active Technologies
        </h3>

        <AnalyticsTable
          headers={["Technology", "Job Demand Count"]}
          data={tableData}
          loading={tableQuery.isLoading}
          error={tableQuery.isError}
          onRetry={tableQuery.refetch}
          renderRow={(row, idx) => (
            <tr key={idx} className="hover:bg-slate-50/40 dark:hover:bg-slate-850/10">
              <td className="px-6 py-3 font-semibold text-slate-900 dark:text-slate-100">
                {row.tech_tag}
              </td>
              <td className="px-6 py-3 font-medium">
                {row.job_demand_count.toLocaleString()}
              </td>
            </tr>
          )}
        />

        {/* Pagination controls */}
        {metadata && (
          <Pagination
            page={page}
            pageSize={pageSize}
            totalPages={metadata.total_pages}
            onPageChange={(p) => updateParams({ page: p })}
            onPageSizeChange={(sz) => updateParams({ page_size: sz })}
            hasPrevious={metadata.has_previous}
            hasNext={metadata.has_next}
          />
        )}
      </div>
    </div>
  );
}
export { Technology };
