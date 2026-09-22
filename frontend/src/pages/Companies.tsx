import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  BuildingOffice2Icon,
  MapPinIcon,
  InformationCircleIcon,
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
import { getCompanies } from "../api/companies";

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
  formatDate,
  truncateText,
} from "../utils/formatters";
import type { CompanyAnalytics } from "../types/api";

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

export default function Companies() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Extract parameters from URL
  const search = searchParams.get("search") || "";
  const sortBy = searchParams.get("sort_by") || "total_jobs";
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
    // Reset to page 1 if search/sort/pageSize is updated
    if (!newParams.page && (newParams.search !== undefined || newParams.sort_by !== undefined || newParams.page_size !== undefined)) {
      updated.set("page", "1");
    }
    setSearchParams(updated);
  };

  // Queries
  const chartCompaniesQuery = useQuery({
    queryKey: ["companies_chart"],
    queryFn: () =>
      getCompanies({
        page_size: 15,
        sort_by: "total_jobs",
        sort_order: "desc",
      }),
  });

  const tableQuery = useQuery({
    queryKey: ["companies_table", { search, sortBy, sortOrder, page, pageSize }],
    queryFn: () =>
      getCompanies({
        search,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: pageSize,
      }),
  });

  const refetchAll = () => {
    chartCompaniesQuery.refetch();
    tableQuery.refetch();
  };

  const isRefreshing = chartCompaniesQuery.isFetching || tableQuery.isFetching;

  const chartData = chartCompaniesQuery.data?.data || [];
  const tableEnvelope = tableQuery.data;
  const tableData = tableEnvelope?.data || [];
  const metadata = tableEnvelope?.metadata;

  // Derive stats strictly from companies endpoint
  const totalCompaniesRepresented = metadata?.total_records ?? null;
  const topCompanyData = chartData.length > 0 ? chartData[0] : null;
  const highestJobCount = topCompanyData ? `${topCompanyData.company} (${topCompanyData.total_jobs})` : "—";

  // Table column definitions
  const columns: ColumnDef<CompanyAnalytics>[] = [
    {
      key: "company",
      header: "Company",
      render: (item) => (
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-md bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 font-semibold">
            <BuildingOffice2Icon className="w-4 h-4" />
          </div>
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">
              {item.company}
            </div>
            {item.highest_paying_role && (
              <div className="text-[11px] text-slate-400 dark:text-slate-500">
                Top Role: {item.highest_paying_role}
              </div>
            )}
          </div>
        </div>
      ),
    },
    {
      key: "total_jobs",
      header: "Total Jobs",
      align: "center",
      render: (item) => (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300 border border-indigo-200/50 dark:border-indigo-800/40">
          {item.total_jobs}
        </span>
      ),
    },
    {
      key: "unique_locations",
      header: "Locations",
      align: "center",
      render: (item) => (
        <div className="inline-flex items-center space-x-1 text-slate-600 dark:text-slate-300">
          <MapPinIcon className="w-3.5 h-3.5 text-slate-400" />
          <span>{item.unique_locations}</span>
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
      key: "latest_posting",
      header: "Latest Posting",
      render: (item) => (
        <span className="text-xs text-slate-500 dark:text-slate-400">
          {item.latest_posting ? formatDate(item.latest_posting) : "—"}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Companies"
        subtitle="Company-level hiring activity across the CareerPulse dataset."
        actions={
          <button
            onClick={refetchAll}
            disabled={isRefreshing}
            className="inline-flex items-center px-3.5 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg shadow-2xs transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Refresh company data"
          >
            <ArrowPathIcon className={`w-3.5 h-3.5 mr-1.5 ${isRefreshing ? "animate-spin text-indigo-600" : ""}`} />
            Refresh
          </button>
        }
      />

      {/* Cumulative Dimension Disclaimer Notice */}
      <div className="flex items-start p-3.5 rounded-lg border border-amber-200/80 bg-amber-50/70 dark:bg-amber-950/20 dark:border-amber-900/40 text-amber-800 dark:text-amber-300 text-xs leading-relaxed">
        <InformationCircleIcon className="w-5 h-5 mr-2.5 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
        <div>
          <strong className="font-semibold">Dataset Semantics Notice:</strong> The company directory reflects{" "}
          <strong>{totalCompaniesRepresented !== null ? `${formatNumber(totalCompaniesRepresented)} cumulative hiring organizations` : "cumulative organizations"}</strong> recorded across ingestion history. Listings represent company-level aggregations across monitored partitions.
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <StatCard
          title="Companies Represented"
          value={totalCompaniesRepresented !== null ? formatNumber(totalCompaniesRepresented) : "—"}
          description="Cumulative organizations tracked"
          icon={BuildingOffice2Icon}
          loading={tableQuery.isLoading}
        />
        <StatCard
          title="Highest Job Count"
          value={highestJobCount}
          description="Top employer by active listings"
          icon={BuildingOffice2Icon}
          loading={chartCompaniesQuery.isLoading}
        />
      </div>

      {/* Top 15 Hiring Companies Horizontal Bar Chart */}
      <ChartCard
        title="Top 15 Hiring Organizations"
        subtitle="Ranked by total open job volume across the monitored market"
        loading={chartCompaniesQuery.isLoading}
        error={chartCompaniesQuery.isError}
        errorMessage="Failed to load company chart records."
        empty={chartData.length === 0}
        emptyMessage="No company hiring records available."
        onRetry={chartCompaniesQuery.refetch}
      >
        <ResponsiveContainer width="100%" height={340}>
          <BarChart
            layout="vertical"
            data={chartData.slice(0, 15).map((d) => ({
              ...d,
              truncatedName: truncateText(d.company, 22),
            }))}
            margin={{ top: 10, right: 30, left: 130, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal vertical={false} stroke="#e2e8f0" className="dark:opacity-15" />
            <XAxis type="number" tick={{ fontSize: 11, fill: "#64748b" }} allowDecimals={false} />
            <YAxis
              dataKey="truncatedName"
              type="category"
              tick={{ fontSize: 11, fill: "#64748b" }}
              width={125}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="total_jobs" name="Total Jobs" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={16} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Search and Sort Toolbar */}
      <FilterBar>
        <SearchBox
          value={search}
          onChange={(val) => updateParams({ search: val })}
          placeholder="Search companies..."
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
            <option value="total_jobs">Total Jobs</option>
            <option value="company">Company Name</option>
            <option value="unique_locations">Locations Count</option>
            <option value="latest_posting">Latest Posting</option>
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

      {/* Main Companies DataTable */}
      <DataTable
        columns={columns}
        data={tableData}
        keyExtractor={(item) => item.company}
        loading={tableQuery.isLoading}
        error={tableQuery.error}
        onRetry={tableQuery.refetch}
        emptyTitle="No companies found"
        emptyMessage={
          search
            ? `No companies matching "${search}" were found in the dataset.`
            : "No hiring companies currently recorded."
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
