import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  GlobeAltIcon,
  MapPinIcon,
  BuildingOfficeIcon,
  ComputerDesktopIcon,
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
import { getGeography } from "../api/geography";

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
import type { GeographyAnalytics } from "../types/api";

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

export default function Geography() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Query geography dataset
  const geographyQuery = useQuery({
    queryKey: ["geography_full"],
    queryFn: () => getGeography(),
  });

  const refetchAll = () => {
    geographyQuery.refetch();
  };

  const isRefreshing = geographyQuery.isFetching;

  const geoData = geographyQuery.data?.data || [];

  // Summary Metrics derived strictly from the complete geography dataset
  const totalBuckets = geoData.length;
  const uniqueCountries = new Set(geoData.map((g) => g.country.trim())).size;

  const largestBucket = geoData.length > 0 ? geoData[0] : null;
  const largestBucketLabel = largestBucket
    ? `${largestBucket.country} (${largestBucket.jobs_count})`
    : "—";

  const totalRemoteJobs = geoData.reduce(
    (acc, curr) => acc + (curr.remote_count || 0),
    0
  );

  // Filtering
  const q = search.trim().toLowerCase();
  const filteredData = q
    ? geoData.filter(
        (item) =>
          item.country.toLowerCase().includes(q) ||
          item.region.toLowerCase().includes(q)
      )
    : geoData;

  // Pagination slice
  const start = (page - 1) * pageSize;
  const paginatedData = filteredData.slice(start, start + pageSize);
  const totalPages = Math.ceil(filteredData.length / pageSize) || 1;

  // Chart data: Top 10 by jobs count
  const chartData = geoData.slice(0, 10).map((d) => ({
    ...d,
    displayName: truncateText(`${d.country}${d.region && d.region !== d.country ? ` (${d.region})` : ""}`, 22),
  }));

  // Table column definitions
  const columns: ColumnDef<GeographyAnalytics>[] = [
    {
      key: "country",
      header: "Country",
      render: (item) => (
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-md bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 font-semibold">
            <GlobeAltIcon className="w-4 h-4" />
          </div>
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">
              {item.country}
            </div>
            {item.region && item.region !== item.country && (
              <div className="text-[11px] text-slate-400 dark:text-slate-500">
                Region: {item.region}
              </div>
            )}
          </div>
        </div>
      ),
    },
    {
      key: "jobs_count",
      header: "Jobs Count",
      align: "center",
      render: (item) => (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200/50 dark:border-emerald-800/40">
          {item.jobs_count}
        </span>
      ),
    },
    {
      key: "company_count",
      header: "Companies",
      align: "center",
      render: (item) => (
        <div className="inline-flex items-center space-x-1 text-slate-600 dark:text-slate-300">
          <BuildingOfficeIcon className="w-3.5 h-3.5 text-slate-400" />
          <span>{item.company_count}</span>
        </div>
      ),
    },
    {
      key: "remote_count",
      header: "Remote Listings",
      align: "center",
      render: (item) => (
        <span className="text-slate-700 dark:text-slate-300 font-medium">
          {item.remote_count}
        </span>
      ),
    },
    {
      key: "onsite_count",
      header: "Onsite Listings",
      align: "center",
      render: (item) => (
        <span className="text-slate-500 dark:text-slate-400">
          {item.onsite_count}
        </span>
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
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Geographic Distribution"
        subtitle="Regional job market density across monitored global locations."
        actions={
          <button
            onClick={refetchAll}
            disabled={isRefreshing}
            className="inline-flex items-center px-3.5 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg shadow-2xs transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Refresh geography data"
          >
            <ArrowPathIcon className={`w-3.5 h-3.5 mr-1.5 ${isRefreshing ? "animate-spin text-indigo-600" : ""}`} />
            Refresh
          </button>
        }
      />

      {/* Mandatory Cumulative Analytics Disclaimer Banner */}
      <div className="flex items-start p-3.5 rounded-lg border border-amber-200/80 bg-amber-50/70 dark:bg-amber-950/20 dark:border-amber-900/40 text-amber-800 dark:text-amber-300 text-xs leading-relaxed">
        <InformationCircleIcon className="w-5 h-5 mr-2.5 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
        <div>
          <strong className="font-semibold">Dataset Semantics Notice:</strong> Geographic distribution is based on the cumulative analytics dimension and should not be interpreted as a pure current 99-job snapshot.
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Geographic Buckets"
          value={formatNumber(totalBuckets)}
          description="Country / region groupings"
          icon={MapPinIcon}
          loading={geographyQuery.isLoading}
        />
        <StatCard
          title="Countries Represented"
          value={formatNumber(uniqueCountries)}
          description="Distinct sovereign territories"
          icon={GlobeAltIcon}
          loading={geographyQuery.isLoading}
        />
        <StatCard
          title="Largest Job Bucket"
          value={largestBucketLabel}
          description="Top hiring geographic market"
          icon={GlobeAltIcon}
          loading={geographyQuery.isLoading}
        />
        <StatCard
          title="Remote Jobs"
          value={formatNumber(totalRemoteJobs)}
          description="Explicitly flexible remote roles"
          icon={ComputerDesktopIcon}
          loading={geographyQuery.isLoading}
        />
      </div>

      {/* Top 10 Geographic Concentrations Horizontal Bar Chart */}
      <ChartCard
        title="Top 10 Geographic Concentrations"
        subtitle="Posting distribution across highest-density regional markets"
        loading={geographyQuery.isLoading}
        error={geographyQuery.isError}
        errorMessage="Failed to load geographic chart records."
        empty={chartData.length === 0}
        emptyMessage="No geographic records available."
        onRetry={geographyQuery.refetch}
      >
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            layout="vertical"
            data={chartData}
            margin={{ top: 10, right: 30, left: 130, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal vertical={false} stroke="#e2e8f0" className="dark:opacity-15" />
            <XAxis type="number" tick={{ fontSize: 11, fill: "#64748b" }} allowDecimals={false} />
            <YAxis
              dataKey="displayName"
              type="category"
              tick={{ fontSize: 11, fill: "#64748b" }}
              width={125}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="jobs_count" name="Jobs Count" fill="#10b981" radius={[0, 4, 4, 0]} barSize={16} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Filter and Search Bar */}
      <FilterBar>
        <div className="w-full sm:w-auto flex-1">
          <SearchBox
            value={search}
            onChange={(val) => {
              setSearch(val);
              setPage(1);
            }}
            placeholder="Filter by country or region..."
          />
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1 pl-1">
            Client-side filter across the complete geography dataset (106 records)
          </p>
        </div>
        <div className="text-xs text-slate-500 dark:text-slate-400">
          Showing {filteredData.length} of {totalBuckets} locations
        </div>
      </FilterBar>

      {/* Main Geography DataTable */}
      <DataTable
        columns={columns}
        data={paginatedData}
        keyExtractor={(item) => `${item.country}-${item.region}`}
        loading={geographyQuery.isLoading}
        error={geographyQuery.error}
        onRetry={geographyQuery.refetch}
        emptyTitle="No geographic buckets found"
        emptyMessage={
          search
            ? `No locations matching "${search}" were found in the dataset.`
            : "No geographic records currently recorded."
        }
        pagination={{
          currentPage: page,
          pageSize: pageSize,
          totalPages: totalPages,
          totalRecords: filteredData.length,
          hasNext: page < totalPages,
          hasPrevious: page > 1,
          onPageChange: (newPage) => setPage(newPage),
          onPageSizeChange: (newPageSize) => {
            setPageSize(newPageSize);
            setPage(1);
          },
        }}
      />
    </div>
  );
}
