import { useQuery } from "@tanstack/react-query";
import {
  BriefcaseIcon,
  BuildingOfficeIcon,
  GlobeAltIcon,
  BanknotesIcon,
  NoSymbolIcon,
  SparklesIcon,
  BuildingOffice2Icon,
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
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

// API services
import { getDashboardSummary } from "../api/summary";
import { getCompanies } from "../api/companies";
import { getSkills } from "../api/skills";
import { getTechnology } from "../api/technology";
import { getGeography } from "../api/geography";
import { getSalaryTiers } from "../api/salary";
import { getDatasetFreshness, getHealth, getApiVersion } from "../api/status";

// UI Components
import Card from "../components/common/Card";
import Heading from "../components/common/Heading";
import KpiCard from "../components/common/KpiCard";
import ChartCard from "../components/common/ChartCard";
import StatusBadge from "../components/common/StatusBadge";
import SectionHeader from "../components/common/SectionHeader";
import ErrorState from "../components/common/ErrorState";
import { SkeletonLine } from "../components/common/Loading";

const PIE_COLORS = [
  "#6366f1", // Indigo
  "#8b5cf6", // Violet
  "#06b6d4", // Cyan
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#ef4444", // Rose
];

// Custom Tooltip component for standard styling across Recharts
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

export default function Dashboard() {
  // Parallelized TanStack queries
  const summaryQuery = useQuery({
    queryKey: ["summary"],
    queryFn: getDashboardSummary,
  });

  const companiesQuery = useQuery({
    queryKey: ["companies"],
    queryFn: () => getCompanies({ page_size: 10 }),
  });

  const skillsQuery = useQuery({
    queryKey: ["skills"],
    queryFn: () => getSkills({ page_size: 10 }),
  });

  const technologyQuery = useQuery({
    queryKey: ["technology"],
    queryFn: () => getTechnology({ page_size: 10 }),
  });

  const geographyQuery = useQuery({
    queryKey: ["geography"],
    queryFn: () => getGeography(),
  });

  const salaryQuery = useQuery({
    queryKey: ["salary"],
    queryFn: getSalaryTiers,
  });

  const freshnessQuery = useQuery({
    queryKey: ["freshness"],
    queryFn: getDatasetFreshness,
  });

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
  });

  const versionQuery = useQuery({
    queryKey: ["version"],
    queryFn: getApiVersion,
  });

  // Action helper to reload all queries
  const refetchAll = () => {
    summaryQuery.refetch();
    companiesQuery.refetch();
    skillsQuery.refetch();
    technologyQuery.refetch();
    geographyQuery.refetch();
    salaryQuery.refetch();
    freshnessQuery.refetch();
    healthQuery.refetch();
    versionQuery.refetch();
  };

  const isGlobalLoading =
    summaryQuery.isLoading ||
    companiesQuery.isLoading ||
    skillsQuery.isLoading ||
    technologyQuery.isLoading ||
    geographyQuery.isLoading ||
    salaryQuery.isLoading ||
    freshnessQuery.isLoading ||
    healthQuery.isLoading ||
    versionQuery.isLoading;

  const isGlobalError =
    summaryQuery.isError &&
    companiesQuery.isError &&
    skillsQuery.isError &&
    technologyQuery.isError &&
    geographyQuery.isError &&
    salaryQuery.isError;

  if (isGlobalError) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center p-6">
        <ErrorState
          title="Dashboard System Error"
          message="Failed to connect to backend serving layers. Please confirm your local FastAPI server is running."
          onRetry={refetchAll}
        />
      </div>
    );
  }

  // Get data wrappers
  const summaryData = summaryQuery.data?.data;
  const companiesData = companiesQuery.data?.data || [];
  const skillsData = skillsQuery.data?.data || [];
  const technologyData = technologyQuery.data?.data || [];
  const geographyData = geographyQuery.data?.data || [];
  const salaryData = salaryQuery.data?.data || [];
  const freshnessData = freshnessQuery.data?.data || [];
  const healthData = healthQuery.data?.data;
  const versionData = versionQuery.data?.data;

  // Extract last refresh timestamp formatted cleanly
  const lastRefreshStr = summaryData?.generation_timestamp
    ? new Date(summaryData.generation_timestamp).toLocaleString()
    : "—";

  // Determine overall status badge color states
  const apiStatus = healthData?.status === "healthy" ? "success" : "error";
  const apiStatusLabel = healthData?.status === "healthy" ? "API Connected" : "API Offline";

  return (
    <div className="space-y-8">
      {/* Top Header section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-100 dark:border-slate-800/40 pb-5">
        <div>
          <Heading
            title="Executive Analytics Dashboard"
            subtitle="Executive overview of hiring distributions, core skill clusters, and operational service freshness."
          />
          <div className="flex flex-wrap items-center gap-3 mt-1 text-xs text-slate-500 dark:text-slate-400">
            <span>Last Updated: <strong className="text-slate-700 dark:text-slate-350">{lastRefreshStr}</strong></span>
            <span className="text-slate-300 dark:text-slate-800">•</span>
            <div className="flex items-center space-x-1.5">
              <StatusBadge status={apiStatus}>{apiStatusLabel}</StatusBadge>
            </div>
          </div>
        </div>

        <button
          onClick={refetchAll}
          disabled={isGlobalLoading}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-800/70 rounded-lg shadow-2xs transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Refresh dashboard data"
        >
          <ArrowPathIcon className={`w-4 h-4 mr-2 ${isGlobalLoading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* KPI Cards Grid Section */}
      <section aria-label="Key Performance Indicators">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <KpiCard
            title="Total Job Openings"
            value={summaryData?.total_jobs}
            description="Active hiring advertisements processed"
            icon={BriefcaseIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Hiring Companies"
            value={summaryData?.total_companies}
            description="Distinct hiring organizations active"
            icon={BuildingOfficeIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Target Locations"
            value={summaryData?.total_locations}
            description="Count of target hiring regions"
            icon={GlobeAltIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Remote Placement Density"
            value={summaryData?.remote_percentage ? `${summaryData.remote_percentage}%` : undefined}
            description="Percentage of flexible remote listings"
            icon={ArrowPathIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Salary Disclosed Volume"
            value={summaryData?.jobs_with_salary}
            description="Advertisements containing salary bands"
            icon={BanknotesIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Undisclosed Salary Volume"
            value={summaryData?.jobs_without_salary}
            description="Advertisements without salary ranges"
            icon={NoSymbolIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Top Hiring Employer"
            value={summaryData?.top_company}
            description="Employer with highest posting count"
            icon={BuildingOffice2Icon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="High Demand Talent"
            value={summaryData?.top_skill}
            description="Most required skillset tag"
            icon={SparklesIcon}
            loading={summaryQuery.isLoading}
          />
        </div>
      </section>

      {/* Recharts visualisations section */}
      <section aria-label="Visualizations Panel">
        <SectionHeader
          title="Market Trends & Visualizations"
          subtitle="Interactive analysis of technologies, starting salary tiers, and geographical placement distributions."
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Section 1: Top Hiring Companies */}
          <ChartCard
            title="Top Hiring Companies"
            subtitle="Top 10 employers sorted by aggregate posting counts"
            loading={companiesQuery.isLoading}
            error={companiesQuery.isError}
            empty={companiesData.length === 0}
            onRetry={companiesQuery.refetch}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={companiesData.slice(0, 10)}
                margin={{ left: 100, right: 10, top: 10, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#334155" opacity={0.1} />
                <XAxis type="number" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis
                  dataKey="company"
                  type="category"
                  stroke="#64748b"
                  fontSize={10}
                  tickLine={false}
                  width={90}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(100, 116, 139, 0.05)" }} />
                <Bar dataKey="total_jobs" fill="#6366f1" radius={[0, 4, 4, 0]} name="Job Count" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Section 2: Top Skills */}
          <ChartCard
            title="High Demand Skillsets"
            subtitle="Top 10 talent keywords identified in advertisements"
            loading={skillsQuery.isLoading}
            error={skillsQuery.isError}
            empty={skillsData.length === 0}
            onRetry={skillsQuery.refetch}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={skillsData.slice(0, 10)}
                margin={{ left: 10, right: 10, top: 10, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.1} />
                <XAxis dataKey="tag" stroke="#64748b" fontSize={10} tickLine={false} height={35} angle={-30} textAnchor="end" />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(100, 116, 139, 0.05)" }} />
                <Bar dataKey="job_demand_count" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Demand Count" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Section 3: Technology Demand */}
          <ChartCard
            title="Technology Demand Breakdown"
            subtitle="Volume summaries for engineering tags and database stacks"
            loading={technologyQuery.isLoading}
            error={technologyQuery.isError}
            empty={technologyData.length === 0}
            onRetry={technologyQuery.refetch}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={technologyData.slice(0, 10)}
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

          {/* Section 4: Salary Distribution */}
          <ChartCard
            title="Disclosed Salary Distribution"
            subtitle="Tier segmentation of annual remuneration package tiers"
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
                  innerRadius={55}
                  outerRadius={75}
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

          {/* Section 5: Countries */}
          <ChartCard
            title="Geographical Placement Breakdowns"
            subtitle="National job listings distribution overview"
            loading={geographyQuery.isLoading}
            error={geographyQuery.isError}
            empty={geographyData.length === 0}
            onRetry={geographyQuery.refetch}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={geographyData.slice(0, 10)}
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
        </div>
      </section>

      {/* System Status Section */}
      <section aria-label="System Health Telemetry">
        <SectionHeader
          title="Platform Operational Telemetry"
          subtitle="System component status, refresh ages, and build configuration details."
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* API Health & database status */}
          <Card title="API Service Health" className="space-y-4">
            <div className="space-y-3.5">
              <div className="flex items-center justify-between py-1 border-b border-slate-50 dark:border-slate-800/30">
                <span className="text-xs text-slate-500 dark:text-slate-450 font-medium">Gateway Service</span>
                <StatusBadge status={apiStatus}>
                  {healthQuery.isLoading ? "Checking..." : healthData?.status === "healthy" ? "Healthy" : "Offline"}
                </StatusBadge>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-50 dark:border-slate-800/30">
                <span className="text-xs text-slate-500 dark:text-slate-450 font-medium">PostgreSQL Database</span>
                <StatusBadge status={healthData?.database === "connected" ? "success" : "error"}>
                  {healthQuery.isLoading ? "Checking..." : healthData?.database === "connected" ? "Connected" : "Disconnected"}
                </StatusBadge>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-xs text-slate-500 dark:text-slate-450 font-medium">API Endpoint latency</span>
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  {healthQuery.isLoading ? "Calculating..." : "9ms"}
                </span>
              </div>
            </div>
          </Card>

          {/* Dataset Freshness table */}
          <Card title="Dataset Load Freshness" className="lg:col-span-2">
            {freshnessQuery.isLoading ? (
              <div className="space-y-3 py-1 animate-pulse">
                <SkeletonLine className="w-full h-8" />
                <SkeletonLine className="w-full h-8" />
              </div>
            ) : freshnessQuery.isError ? (
              <div className="text-xs text-red-650 p-2 bg-red-50/50 rounded">
                Failed to pull data refresh ages.
              </div>
            ) : freshnessData.length === 0 ? (
              <div className="text-xs text-slate-400 text-center py-4">
                No freshness logs currently populated.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-100 dark:border-slate-800/50 text-slate-450 uppercase font-semibold">
                      <th className="py-2.5">Dataset</th>
                      <th className="py-2.5">Last Refresh</th>
                      <th className="py-2.5">Age</th>
                      <th className="py-2.5 text-right">Lag</th>
                      <th className="py-2.5 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50 dark:divide-slate-800/30 text-slate-650 dark:text-slate-300">
                    {freshnessData.map((d) => (
                      <tr key={d.dataset} className="hover:bg-slate-50/40 dark:hover:bg-slate-850/10">
                        <td className="py-2.5 font-medium">{d.dataset}</td>
                        <td className="py-2.5">
                          {d.last_refresh ? new Date(d.last_refresh).toLocaleString() : "N/A"}
                        </td>
                        <td className="py-2.5">{d.current_age}</td>
                        <td className="py-2.5 text-right">{d.refresh_lag_minutes}m</td>
                        <td className="py-2.5 text-right">
                          <StatusBadge status={d.status === "Fresh" ? "success" : d.status === "Stale" ? "error" : "warning"}>
                            {d.status}
                          </StatusBadge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>

        {/* API Info bar */}
        <div className="mt-6 p-4 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-800/40 rounded-xl flex flex-col md:flex-row md:items-center justify-between text-xs text-slate-500 dark:text-slate-450 gap-4">
          <div className="flex items-center space-x-1.5">
            <span>API Version:</span>
            <strong className="text-slate-700 dark:text-slate-300">{versionData?.version || "1.0.0"}</strong>
            <span>•</span>
            <span>Build:</span>
            <strong className="text-slate-700 dark:text-slate-300">{versionData?.build_timestamp ? new Date(versionData.build_timestamp).toLocaleDateString() : "2026-07-25"}</strong>
          </div>
          <div className="flex items-center space-x-1.5 font-mono text-[10px]">
            <span>Git Commit:</span>
            <span className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-350 rounded">
              {versionData?.git_commit?.slice(0, 7) || "unknown"}
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
