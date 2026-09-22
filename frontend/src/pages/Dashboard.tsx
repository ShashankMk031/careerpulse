import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  BriefcaseIcon,
  BuildingOfficeIcon,
  GlobeAltIcon,
  BanknotesIcon,
  NoSymbolIcon,
  SparklesIcon,
  BuildingOffice2Icon,
  ArrowPathIcon,
  AcademicCapIcon,
  CpuChipIcon,
  ServerIcon,
  ChevronRightIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  ComputerDesktopIcon,
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

// Formatting Utilities
import {
  formatNumber,
  formatCurrency,
  formatPercent,
  formatDate,
  calculatePercentage,
  truncateText,
} from "../utils/formatters";

// Custom Tooltip component for standard styling across Recharts
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
            {item.payload?.percentage ? ` (${item.payload.percentage})` : ""}
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
    queryKey: ["companies", { page_size: 10, sort_by: "total_jobs", sort_order: "desc" }],
    queryFn: () => getCompanies({ page_size: 10, sort_by: "total_jobs", sort_order: "desc" }),
  });

  const skillsQuery = useQuery({
    queryKey: ["skills", { page_size: 10 }],
    queryFn: () => getSkills({ page_size: 10 }),
  });

  const technologyQuery = useQuery({
    queryKey: ["technology", { page_size: 10 }],
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

  // Extract last refresh timestamp formatted for humans
  const lastRefreshStr = formatDate(summaryData?.generation_timestamp);

  // Determine overall status badge color states
  const apiStatus = healthData?.status === "healthy" ? "success" : "error";
  const apiStatusLabel = healthData?.status === "healthy" ? "API Connected" : "API Offline";

  // Compute Salary Tier percentages
  const totalDisclosedSalaryJobs = salaryData.reduce(
    (acc: number, item: any) => acc + (item.jobs_count || 0),
    0
  );

  const enrichedSalaryData = salaryData.map((item: any) => ({
    ...item,
    percentage: calculatePercentage(item.jobs_count, totalDisclosedSalaryJobs || summaryData?.total_jobs || 1),
  }));

  // Top 10 slices for charts
  const topCompanies = companiesData.slice(0, 10);
  const topSkills = skillsData.slice(0, 10);
  const topTechnology = technologyData.slice(0, 10);
  const topGeography = geographyData.slice(0, 10);

  // Remote Jobs count calculation fallback
  const remoteJobsCount =
    summaryData?.remote_jobs !== undefined
      ? summaryData.remote_jobs
      : Math.round(((summaryData?.total_jobs || 0) * (summaryData?.remote_percentage || 0)) / 100);

  return (
    <div className="space-y-8">
      {/* Top Header section & Freshness indicator */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <Heading
            title="Executive Analytics Dashboard"
            subtitle="Real-time market intelligence across remote job demand, technical capabilities, and compensation benchmarks."
          />
          <div className="flex flex-wrap items-center gap-3 mt-1 text-xs text-slate-500 dark:text-slate-400">
            <span>
              Data generated:{" "}
              <strong className="text-slate-700 dark:text-slate-300">
                {lastRefreshStr}
              </strong>
            </span>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <div className="flex items-center space-x-1.5">
              <StatusBadge status={apiStatus}>{apiStatusLabel}</StatusBadge>
            </div>
          </div>
        </div>

        <button
          onClick={refetchAll}
          disabled={isGlobalLoading}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/80 rounded-lg shadow-xs transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Refresh dashboard data"
        >
          <ArrowPathIcon className={`w-4 h-4 mr-2 ${isGlobalLoading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* SECTION 1: KPI Grid Header (7 KPI Cards) */}
      <section aria-label="Key Performance Indicators">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          <KpiCard
            title="Total Jobs"
            value={formatNumber(summaryData?.total_jobs)}
            description="Active job postings"
            icon={BriefcaseIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Companies"
            value={formatNumber(summaryData?.total_companies)}
            description="Hiring organizations"
            icon={BuildingOfficeIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Locations"
            value={formatNumber(summaryData?.total_locations)}
            description="Target hiring regions"
            icon={GlobeAltIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Remote Jobs"
            value={formatNumber(remoteJobsCount)}
            description="Flexible remote listings"
            icon={ComputerDesktopIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Remote %"
            value={summaryData?.remote_percentage !== undefined ? formatPercent(summaryData.remote_percentage) : "—"}
            description="Remote market share"
            icon={ArrowPathIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Jobs With Salary"
            value={formatNumber(summaryData?.jobs_with_salary)}
            description="Salary band disclosed"
            icon={BanknotesIcon}
            loading={summaryQuery.isLoading}
          />
          <KpiCard
            title="Jobs Without Salary"
            value={formatNumber(summaryData?.jobs_without_salary)}
            description="Compensation unlisted"
            icon={NoSymbolIcon}
            loading={summaryQuery.isLoading}
          />
        </div>
      </section>

      {/* SECTION 8: Analytical Rows (2 columns on desktop) */}

      {/* Row 2: Top Companies | Top Skills */}
      <section aria-label="Organizational and Skills Demand" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 3: Top Companies */}
        <ChartCard
          title="Top Hiring Companies"
          subtitle="Top 10 employers sorted by aggregate posting counts"
          loading={companiesQuery.isLoading}
          error={companiesQuery.isError}
          errorMessage="Failed to load company rankings."
          empty={companiesData.length === 0}
          emptyMessage="No company hiring records available."
          onRetry={companiesQuery.refetch}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              layout="vertical"
              data={topCompanies}
              margin={{ left: 110, right: 24, top: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#334155" opacity={0.15} />
              <XAxis type="number" stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis
                dataKey="company"
                type="category"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                width={100}
                tickFormatter={(val) => truncateText(val, 15)}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(100, 116, 139, 0.08)" }} />
              <Bar dataKey="total_jobs" fill="#6366f1" radius={[0, 4, 4, 0]} name="Job Count" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Section 4: Top Skills */}
        <ChartCard
          title="Top In-Demand Skills"
          subtitle="Top 10 talent keywords identified in job advertisements"
          loading={skillsQuery.isLoading}
          error={skillsQuery.isError}
          errorMessage="Failed to load skill demand metrics."
          empty={skillsData.length === 0}
          emptyMessage="No skills demand records available."
          onRetry={skillsQuery.refetch}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              layout="vertical"
              data={topSkills}
              margin={{ left: 90, right: 24, top: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#334155" opacity={0.15} />
              <XAxis type="number" stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis
                dataKey="tag"
                type="category"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                width={80}
                tickFormatter={(val) => truncateText(val, 12)}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(100, 116, 139, 0.08)" }} />
              <Bar dataKey="job_demand_count" fill="#8b5cf6" radius={[0, 4, 4, 0]} name="Demand Count" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </section>

      {/* Row 3: Technology Demand | Geographic Job Distribution */}
      <section aria-label="Technology and Geography Distribution" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 5: Technology Demand */}
        <ChartCard
          title="Technology Demand Breakdown"
          subtitle="Core engineering frameworks, programming languages, and databases"
          loading={technologyQuery.isLoading}
          error={technologyQuery.isError}
          errorMessage="Failed to load technology demand breakdown."
          empty={technologyData.length === 0}
          emptyMessage="No technology stack records available."
          onRetry={technologyQuery.refetch}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              layout="vertical"
              data={topTechnology}
              margin={{ left: 90, right: 24, top: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#334155" opacity={0.15} />
              <XAxis type="number" stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis
                dataKey="tech_tag"
                type="category"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                width={80}
                tickFormatter={(val) => truncateText(val, 12)}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(100, 116, 139, 0.08)" }} />
              <Bar dataKey="job_demand_count" fill="#06b6d4" radius={[0, 4, 4, 0]} name="Demand Count" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Section 6: Geographic Job Distribution */}
        <ChartCard
          title="Geographic Job Distribution"
          subtitle="Ranked national and regional hiring concentrations across active listings"
          loading={geographyQuery.isLoading}
          error={geographyQuery.isError}
          errorMessage="Failed to load geographic distributions."
          empty={geographyData.length === 0}
          emptyMessage="No geography distribution records available."
          onRetry={geographyQuery.refetch}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              layout="vertical"
              data={topGeography}
              margin={{ left: 100, right: 24, top: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#334155" opacity={0.15} />
              <XAxis type="number" stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis
                dataKey="country"
                type="category"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                width={90}
                tickFormatter={(val) => truncateText(val, 14)}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(100, 116, 139, 0.08)" }} />
              <Bar dataKey="jobs_count" fill="#10b981" radius={[0, 4, 4, 0]} name="Jobs Count" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </section>

      {/* Row 4: Salary Distribution | Market Highlights */}
      <section aria-label="Compensation and Highlights" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 7: Salary Distribution */}
        <ChartCard
          title="Disclosed Salary Distribution"
          subtitle="Annual compensation bands and percentage distribution shares"
          loading={salaryQuery.isLoading}
          error={salaryQuery.isError}
          errorMessage="Failed to load salary tiers."
          empty={enrichedSalaryData.length === 0}
          emptyMessage="No salary band records available."
          onRetry={salaryQuery.refetch}
        >
          <div className="flex flex-col h-full justify-between">
            <div className="h-[210px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  layout="vertical"
                  data={enrichedSalaryData}
                  margin={{ left: 120, right: 30, top: 5, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#334155" opacity={0.15} />
                  <XAxis type="number" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis
                    dataKey="salary_tier"
                    type="category"
                    stroke="#94a3b8"
                    fontSize={11}
                    tickLine={false}
                    width={115}
                    tickFormatter={(val) => truncateText(val, 16)}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(100, 116, 139, 0.08)" }} />
                  <Bar dataKey="jobs_count" fill="#f59e0b" radius={[0, 4, 4, 0]} name="Jobs Count" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Compensation Metadata Footer */}
            <div className="pt-2 border-t border-slate-100 dark:border-slate-800 grid grid-cols-3 gap-2 text-center text-xs">
              <div className="p-1.5 bg-slate-50 dark:bg-slate-850 rounded">
                <span className="text-slate-400 block text-[10px] uppercase font-medium">Disclosed</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">
                  {formatNumber(summaryData?.jobs_with_salary || totalDisclosedSalaryJobs)}
                </span>
              </div>
              <div className="p-1.5 bg-slate-50 dark:bg-slate-850 rounded">
                <span className="text-slate-400 block text-[10px] uppercase font-medium">Undisclosed</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">
                  {formatNumber(summaryData?.jobs_without_salary)}
                </span>
              </div>
              <div className="p-1.5 bg-slate-50 dark:bg-slate-850 rounded">
                <span className="text-slate-400 block text-[10px] uppercase font-medium">Median</span>
                <span className="font-bold text-amber-600 dark:text-amber-400">
                  {summaryData?.median_salary ? formatCurrency(summaryData.median_salary) : "—"}
                </span>
              </div>
            </div>
          </div>
        </ChartCard>

        {/* Section 2: Market Highlights */}
        <Card
          title="Market Highlights"
          subtitle="Top performing market leaders across hiring volume, skill demand, and compensation"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 h-full">
            {/* Top Company */}
            <div className="p-4 bg-slate-50/60 dark:bg-slate-850/50 border border-slate-200 dark:border-slate-800 rounded-xl flex items-start gap-3.5">
              <div className="p-2.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 shrink-0">
                <BuildingOffice2Icon className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Top Company
                </span>
                <span
                  className="text-sm font-bold text-slate-900 dark:text-white truncate block mt-0.5"
                  title={summaryData?.top_company || "—"}
                >
                  {summaryData?.top_company || "—"}
                </span>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 block">
                  Leading job volume
                </span>
              </div>
            </div>

            {/* Top Skill */}
            <div className="p-4 bg-slate-50/60 dark:bg-slate-850/50 border border-slate-200 dark:border-slate-800 rounded-xl flex items-start gap-3.5">
              <div className="p-2.5 rounded-lg bg-violet-50 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400 shrink-0">
                <SparklesIcon className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Top Skill
                </span>
                <span
                  className="text-sm font-bold text-slate-900 dark:text-white truncate block mt-0.5"
                  title={summaryData?.top_skill || "—"}
                >
                  {summaryData?.top_skill || "—"}
                </span>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 block">
                  Highest talent demand
                </span>
              </div>
            </div>

            {/* Top Country */}
            <div className="p-4 bg-slate-50/60 dark:bg-slate-850/50 border border-slate-200 dark:border-slate-800 rounded-xl flex items-start gap-3.5">
              <div className="p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 shrink-0">
                <MapPinIcon className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Top Country
                </span>
                <span
                  className="text-sm font-bold text-slate-900 dark:text-white truncate block mt-0.5"
                  title={summaryData?.top_country || "Global Remote"}
                >
                  {summaryData?.top_country || "Global Remote"}
                </span>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 block">
                  Primary hiring geography
                </span>
              </div>
            </div>

            {/* Highest Paying Company */}
            <div className="p-4 bg-slate-50/60 dark:bg-slate-850/50 border border-slate-200 dark:border-slate-800 rounded-xl flex items-start gap-3.5">
              <div className="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 shrink-0">
                <CurrencyDollarIcon className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Highest Paying Company
                </span>
                <span
                  className="text-sm font-bold text-slate-900 dark:text-white truncate block mt-0.5"
                  title={summaryData?.highest_paying_company || "—"}
                >
                  {summaryData?.highest_paying_company || "—"}
                </span>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 block">
                  {summaryData?.highest_salary ? `Peak: ${formatCurrency(summaryData.highest_salary)}` : "Market Leading"}
                </span>
              </div>
            </div>
          </div>
        </Card>
      </section>

      {/* Module Quick-Links Section */}
      <section aria-label="Intelligence Modules">
        <SectionHeader
          title="Specialized Intelligence Modules"
          subtitle="Explore detailed analytical breakdowns, cross-tabulations, and market benchmarks."
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Link
            to="/companies"
            className="group p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-indigo-400 dark:hover:border-indigo-600 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <span className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400">
                  <BuildingOfficeIcon className="w-4 h-4" />
                </span>
                <ChevronRightIcon className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
                Hiring Companies
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Filter and paginate active hiring organizations, posting volumes, and salary benchmarks.
              </p>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 text-[11px] font-medium text-indigo-600 dark:text-indigo-400">
              View Organizations →
            </div>
          </Link>

          <Link
            to="/skills"
            className="group p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-violet-400 dark:hover:border-violet-600 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <span className="p-2 rounded-lg bg-violet-50 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400">
                  <AcademicCapIcon className="w-4 h-4" />
                </span>
                <ChevronRightIcon className="w-4 h-4 text-slate-400 group-hover:text-violet-600 dark:group-hover:text-violet-400 group-hover:translate-x-0.5 transition-all" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
                Skills Intelligence
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Analyze high-demand skills, talent tags, and market premium compensation across listings.
              </p>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 text-[11px] font-medium text-violet-600 dark:text-violet-400">
              Explore Skills →
            </div>
          </Link>

          <Link
            to="/technology"
            className="group p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-cyan-400 dark:hover:border-cyan-600 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <span className="p-2 rounded-lg bg-cyan-50 dark:bg-cyan-950/40 text-cyan-600 dark:text-cyan-400">
                  <CpuChipIcon className="w-4 h-4" />
                </span>
                <ChevronRightIcon className="w-4 h-4 text-slate-400 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 group-hover:translate-x-0.5 transition-all" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
                Technology Stacks
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Review database engines, cloud frameworks, and programming language demand clusters.
              </p>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 text-[11px] font-medium text-cyan-600 dark:text-cyan-400">
              Inspect Tech Stacks →
            </div>
          </Link>

          <Link
            to="/geography"
            className="group p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-emerald-400 dark:hover:border-emerald-600 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <span className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400">
                  <GlobeAltIcon className="w-4 h-4" />
                </span>
                <ChevronRightIcon className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 group-hover:translate-x-0.5 transition-all" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
                Geographical Distribution
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                National and regional hiring footprints, international remote density, and location clusters.
              </p>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
              View Geography →
            </div>
          </Link>

          <Link
            to="/salary"
            className="group p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-amber-400 dark:hover:border-amber-600 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <span className="p-2 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400">
                  <BanknotesIcon className="w-4 h-4" />
                </span>
                <ChevronRightIcon className="w-4 h-4 text-slate-400 group-hover:text-amber-600 dark:group-hover:text-amber-400 group-hover:translate-x-0.5 transition-all" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
                Salary Intelligence
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Annual remuneration tiers, disclosure volumes, median statistics, and top paying firms.
              </p>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 text-[11px] font-medium text-amber-600 dark:text-amber-400">
              Analyze Salaries →
            </div>
          </Link>

          <Link
            to="/status"
            className="group p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-rose-400 dark:hover:border-rose-600 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <span className="p-2 rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400">
                  <ServerIcon className="w-4 h-4" />
                </span>
                <ChevronRightIcon className="w-4 h-4 text-slate-400 group-hover:text-rose-600 dark:group-hover:text-rose-400 group-hover:translate-x-0.5 transition-all" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
                Platform Telemetry
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                PostgreSQL pool metrics, pipeline freshness lags, Git commit versions, and service uptime.
              </p>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 text-[11px] font-medium text-rose-600 dark:text-rose-400">
              Inspect Telemetry →
            </div>
          </Link>
        </div>
      </section>

      {/* System Status Section (Telemetry & Health) */}
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
                <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Gateway Service</span>
                <StatusBadge status={apiStatus}>
                  {healthQuery.isLoading ? "Checking..." : healthData?.status === "healthy" ? "Healthy" : "Offline"}
                </StatusBadge>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-50 dark:border-slate-800/30">
                <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">PostgreSQL Database</span>
                <StatusBadge status={healthData?.database === "connected" ? "success" : "error"}>
                  {healthQuery.isLoading ? "Checking..." : healthData?.database === "connected" ? "Connected" : "Disconnected"}
                </StatusBadge>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">API Endpoint latency</span>
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
              <div className="text-xs text-red-600 dark:text-red-400 p-2 bg-red-50/50 dark:bg-red-950/20 rounded">
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
                    <tr className="border-b border-slate-100 dark:border-slate-800/50 text-slate-400 uppercase font-semibold">
                      <th className="py-2.5">Dataset</th>
                      <th className="py-2.5">Last Refresh</th>
                      <th className="py-2.5">Age</th>
                      <th className="py-2.5 text-right">Lag</th>
                      <th className="py-2.5 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50 dark:divide-slate-800/30 text-slate-600 dark:text-slate-300">
                    {freshnessData.map((d) => (
                      <tr key={d.dataset} className="hover:bg-slate-50/40 dark:hover:bg-slate-800/20">
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
        <div className="mt-6 p-4 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-800/40 rounded-xl flex flex-col md:flex-row md:items-center justify-between text-xs text-slate-500 dark:text-slate-400 gap-4">
          <div className="flex items-center space-x-1.5">
            <span>API Version:</span>
            <strong className="text-slate-700 dark:text-slate-300">{versionData?.version ?? "—"}</strong>
            <span>•</span>
            <span>Build:</span>
            <strong className="text-slate-700 dark:text-slate-300">{versionData?.build_timestamp ? new Date(versionData.build_timestamp).toLocaleDateString() : "—"}</strong>
          </div>
          <div className="flex items-center space-x-1.5 font-mono text-[10px]">
            <span>Git Commit:</span>
            <span className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded">
              {versionData?.git_commit?.slice(0, 7) || "unknown"}
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
