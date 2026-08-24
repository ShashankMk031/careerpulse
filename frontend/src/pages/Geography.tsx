import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  GlobeAltIcon,
  HomeModernIcon,
  ArrowTrendingUpIcon,
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
  Legend,
} from "recharts";

// API services
import { getGeography } from "../api/geography";
import { getDashboardSummary } from "../api/summary";

// UI Components
import Heading from "../components/common/Heading";
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

export default function Geography() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Local pagination state
  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = parseInt(searchParams.get("page_size") || "20", 10);

  const updatePage = (newPage: number) => {
    const updated = new URLSearchParams(searchParams);
    updated.set("page", String(newPage));
    setSearchParams(updated);
  };

  const updatePageSize = (newPageSize: number) => {
    const updated = new URLSearchParams(searchParams);
    updated.set("page_size", String(newPageSize));
    updated.set("page", "1");
    setSearchParams(updated);
  };

  // Queries
  const summaryQuery = useQuery({
    queryKey: ["summary"],
    queryFn: getDashboardSummary,
  });

  const geographyQuery = useQuery({
    queryKey: ["geography_full"],
    queryFn: () => getGeography(),
  });

  const summaryData = summaryQuery.data?.data;
  const geoData = geographyQuery.data?.data || [];

  // Derive stats
  const distinctCountries = geoData.length;
  const remoteJobs = summaryData?.remote_jobs || 0;
  const largestMarket = geoData.length > 0 ? geoData[0].country : "—";

  // Calculate local pagination
  const startIndex = (page - 1) * pageSize;
  const paginatedData = geoData.slice(startIndex, startIndex + pageSize);
  const totalPages = Math.ceil(geoData.length / pageSize);

  return (
    <div className="space-y-6">
      <Heading
        title="Geography & Markets"
        subtitle="Global market distribution, national posting volumes, and remote density mappings."
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <SummaryCard
          title="Active Countries"
          value={distinctCountries}
          description="Distinct national regions active"
          icon={GlobeAltIcon}
          loading={geographyQuery.isLoading}
        />
        <SummaryCard
          title="Remote Job Postings"
          value={remoteJobs.toLocaleString()}
          description="Aggregate flexible work placements"
          icon={HomeModernIcon}
          loading={summaryQuery.isLoading}
        />
        <SummaryCard
          title="Largest Market"
          value={largestMarket}
          description="Country with highest posting volume"
          icon={ArrowTrendingUpIcon}
          loading={geographyQuery.isLoading}
        />
      </div>

      {/* Visualizations grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Country Demand */}
        <ChartCard
          title="Country Market Demand"
          subtitle="Posting count distribution by country"
          loading={geographyQuery.isLoading}
          error={geographyQuery.isError}
          empty={geoData.length === 0}
          onRetry={geographyQuery.refetch}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              layout="vertical"
              data={geoData.slice(0, 10)}
              margin={{ left: 80, right: 10, top: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#334155" opacity={0.1} />
              <XAxis type="number" stroke="#64748b" fontSize={10} tickLine={false} />
              <YAxis
                dataKey="country"
                type="category"
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
                width={75}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(100, 116, 139, 0.05)" }} />
              <Bar dataKey="jobs_count" fill="#10b981" radius={[0, 4, 4, 0]} name="Job Count" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Chart 2: Remote vs Onsite Stacked Bar */}
        <ChartCard
          title="Placement Formats by Country"
          subtitle="Distribution of remote, hybrid, and onsite listings"
          loading={geographyQuery.isLoading}
          error={geographyQuery.isError}
          empty={geoData.length === 0}
          onRetry={geographyQuery.refetch}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={geoData.slice(0, 10)}
              margin={{ left: 10, right: 10, top: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.1} />
              <XAxis dataKey="country" stroke="#64748b" fontSize={10} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: 10 }} />
              <Bar dataKey="remote_count" name="Remote" stackId="a" fill="#10b981" />
              <Bar dataKey="hybrid_count" name="Hybrid" stackId="a" fill="#3b82f6" />
              <Bar dataKey="onsite_count" name="Onsite" stackId="a" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Local Paginated Data Table */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
          Geographical Regions Inventory
        </h3>

        <AnalyticsTable
          headers={["Country", "Region", "Total Jobs", "Remote Placement Volume", "Remote Ratio"]}
          data={paginatedData}
          loading={geographyQuery.isLoading}
          error={geographyQuery.isError}
          onRetry={geographyQuery.refetch}
          renderRow={(row, idx) => {
            const ratio = row.jobs_count > 0 ? ((row.remote_count / row.jobs_count) * 100).toFixed(1) : "0";
            return (
              <tr key={idx} className="hover:bg-slate-50/40 dark:hover:bg-slate-850/10">
                <td className="px-6 py-3 font-semibold text-slate-900 dark:text-slate-100">
                  {row.country}
                </td>
                <td className="px-6 py-3 text-slate-500 dark:text-slate-400">
                  {row.region || "All regions"}
                </td>
                <td className="px-6 py-3 font-medium">
                  {row.jobs_count.toLocaleString()}
                </td>
                <td className="px-6 py-3">
                  {row.remote_count.toLocaleString()}
                </td>
                <td className="px-6 py-3">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-400">
                    {ratio}%
                  </span>
                </td>
              </tr>
            );
          }}
        />

        {totalPages > 1 && (
          <Pagination
            page={page}
            pageSize={pageSize}
            totalPages={totalPages}
            onPageChange={updatePage}
            onPageSizeChange={updatePageSize}
            hasPrevious={page > 1}
            hasNext={page < totalPages}
          />
        )}
      </div>
    </div>
  );
}
export { Geography };
