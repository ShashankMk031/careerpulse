import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ServerIcon,
  CircleStackIcon,
  ClockIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
} from "@heroicons/react/24/outline";

// API services
import { getDatasetFreshness, getHealth, getApiVersion } from "../api/status";

// UI Components
import PageHeader from "../components/common/PageHeader";
import StatCard from "../components/common/StatCard";
import Card from "../components/common/Card";
import StatusBadge from "../components/common/StatusBadge";
import DataTable, { type ColumnDef } from "../components/common/DataTable";

// Formatting
import { formatDate } from "../utils/formatters";
import type { DatasetFreshness } from "../types/api";

export default function Status() {
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

  // Parallel Queries
  const healthQuery = useQuery({
    queryKey: ["health_telemetry"],
    queryFn: getHealth,
  });

  const freshnessQuery = useQuery({
    queryKey: ["freshness_telemetry"],
    queryFn: getDatasetFreshness,
  });

  const versionQuery = useQuery({
    queryKey: ["version_telemetry"],
    queryFn: getApiVersion,
  });

  const refetchAll = () => {
    healthQuery.refetch();
    freshnessQuery.refetch();
    versionQuery.refetch();
    setLastChecked(new Date());
  };

  const isRefreshing = healthQuery.isFetching || freshnessQuery.isFetching || versionQuery.isFetching;

  const healthData = healthQuery.data?.data;
  const freshnessData = freshnessQuery.data?.data || [];
  const versionData = versionQuery.data?.data;

  // Status mappings
  const apiStatus = healthData?.status === "healthy" ? "success" : "error";
  const dbStatus = healthData?.database === "connected" ? "success" : "error";

  // Highest sync lag calculation
  const maxLag =
    freshnessData.length > 0
      ? Math.max(...freshnessData.map((d) => d.refresh_lag_minutes))
      : 0;

  // Telemetry Table column definitions
  const columns: ColumnDef<DatasetFreshness>[] = [
    {
      key: "dataset",
      header: "Lakehouse Dataset",
      render: (item) => (
        <span className="font-semibold text-slate-900 dark:text-white uppercase tracking-wider text-xs">
          gold_{item.dataset}
        </span>
      ),
    },
    {
      key: "status",
      header: "Freshness State",
      align: "center",
      render: (item) => {
        const badgeStatus =
          item.status === "FRESH"
            ? "success"
            : item.status === "STALE"
            ? "warning"
            : "error";
        return <StatusBadge status={badgeStatus}>{item.status}</StatusBadge>;
      },
    },
    {
      key: "refresh_lag_minutes",
      header: "Sync Lag",
      align: "center",
      render: (item) => (
        <span className="font-mono text-xs text-slate-700 dark:text-slate-300">
          {item.refresh_lag_minutes.toFixed(1)} min
        </span>
      ),
    },
    {
      key: "current_age",
      header: "Dataset Age",
      render: (item) => (
        <span className="text-xs text-slate-600 dark:text-slate-400 font-mono">
          {item.current_age.split(".")[0]}
        </span>
      ),
    },
    {
      key: "source_generation_timestamp",
      header: "Source Generation Time",
      render: (item) => (
        <span className="text-xs text-slate-500 dark:text-slate-400">
          {formatDate(item.source_generation_timestamp)}
        </span>
      ),
    },
    {
      key: "last_refresh",
      header: "Last Sync Time",
      render: (item) => (
        <span className="text-xs text-slate-500 dark:text-slate-400">
          {formatDate(item.last_refresh)}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Operations & Freshness"
        subtitle="Operational health checks, database connection pool status, and lakehouse synchronization telemetry."
        actions={
          <div className="flex items-center space-x-3 text-xs text-slate-500 dark:text-slate-400">
            <span>
              Last checked:{" "}
              <strong className="text-slate-700 dark:text-slate-300">
                {lastChecked.toLocaleTimeString()}
              </strong>
            </span>
            <button
              onClick={refetchAll}
              disabled={isRefreshing}
              className="inline-flex items-center px-3.5 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg shadow-2xs transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Refresh telemetry data"
            >
              <ArrowPathIcon className={`w-3.5 h-3.5 mr-1.5 ${isRefreshing ? "animate-spin text-indigo-600" : ""}`} />
              Refresh
            </button>
          </div>
        }
      />

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="API Gateway Status"
          value={healthData?.status ? healthData.status.toUpperCase() : "OFFLINE"}
          description="FastAPI service health check"
          icon={ServerIcon}
          loading={healthQuery.isLoading}
        />
        <StatCard
          title="Database Pool Connection"
          value={healthData?.database ? healthData.database.toUpperCase() : "DISCONNECTED"}
          description="RDS PostgreSQL ThreadedConnectionPool"
          icon={CircleStackIcon}
          loading={healthQuery.isLoading}
        />
        <StatCard
          title="Maximum Pipeline Sync Lag"
          value={`${maxLag.toFixed(1)} min`}
          description="Latest S3 Gold → RDS ingestion delta"
          icon={ClockIcon}
          loading={freshnessQuery.isLoading}
        />
      </div>

      {/* Operational Metadata Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Core telemetry details */}
        <Card title="Runtime & Connectivity Telemetry" subtitle="Gateway endpoints and database session pool state">
          <div className="divide-y divide-slate-100 dark:divide-slate-800/60 text-xs">
            <div className="flex items-center justify-between py-2.5">
              <span className="text-slate-600 dark:text-slate-400 font-medium">Gateway Service</span>
              <StatusBadge status={apiStatus}>
                {healthQuery.isLoading ? "Checking..." : healthData?.status === "healthy" ? "Healthy" : "Offline"}
              </StatusBadge>
            </div>
            <div className="flex items-center justify-between py-2.5">
              <span className="text-slate-600 dark:text-slate-400 font-medium">RDS PostgreSQL Pool</span>
              <StatusBadge status={dbStatus}>
                {healthQuery.isLoading ? "Checking..." : healthData?.database === "connected" ? "Connected" : "Disconnected"}
              </StatusBadge>
            </div>
            <div className="flex items-center justify-between py-2.5">
              <span className="text-slate-600 dark:text-slate-400 font-medium">API Base URL</span>
              <span className="font-mono text-slate-700 dark:text-slate-300">
                http://127.0.0.1:8000
              </span>
            </div>
            <div className="flex items-center justify-between py-2.5">
              <span className="text-slate-600 dark:text-slate-400 font-medium">Serving Schema</span>
              <span className="font-mono text-slate-700 dark:text-slate-300">
                serving_db.serving
              </span>
            </div>
          </div>
        </Card>

        {/* Build & Version Information */}
        <Card title="Application Version & Build Context" subtitle="Verified repository releases and Python runtime environments">
          <div className="divide-y divide-slate-100 dark:divide-slate-800/60 text-xs">
            <div className="flex items-center justify-between py-2.5">
              <span className="text-slate-600 dark:text-slate-400 font-medium">Platform Release</span>
              <span className="font-semibold text-slate-900 dark:text-white">
                {versionQuery.isLoading ? "Loading..." : versionData?.version ? `v${versionData.version}` : "Unavailable"}
              </span>
            </div>
            <div className="flex items-center justify-between py-2.5">
              <span className="text-slate-600 dark:text-slate-400 font-medium">Git Commit SHA</span>
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-indigo-600 dark:text-indigo-400">
                {versionQuery.isLoading ? "..." : versionData?.git_commit ? versionData.git_commit.slice(0, 10) : "Unavailable"}
              </span>
            </div>
            <div className="flex items-center justify-between py-2.5">
              <span className="text-slate-600 dark:text-slate-400 font-medium">Python Runtime</span>
              <span className="font-mono text-slate-700 dark:text-slate-300">
                {versionQuery.isLoading ? "..." : versionData?.python_version ? versionData.python_version.split(" ")[0] : "Unavailable"}
              </span>
            </div>
            <div className="flex items-center justify-between py-2.5">
              <span className="text-slate-600 dark:text-slate-400 font-medium">Build Timestamp</span>
              <span className="text-slate-600 dark:text-slate-400">
                {versionQuery.isLoading ? "..." : versionData?.build_timestamp ? formatDate(versionData.build_timestamp) : "—"}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Dataset Freshness Telemetry Table */}
      <div className="space-y-3">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white">
          Lakehouse Dataset Synchronization Logs
        </h2>
        <DataTable
          columns={columns}
          data={freshnessData}
          keyExtractor={(item) => item.dataset}
          loading={freshnessQuery.isLoading}
          error={freshnessQuery.error}
          onRetry={freshnessQuery.refetch}
          emptyTitle="No dataset synchronization logs"
          emptyMessage="No dataset freshness records currently returned by /metrics."
        />
      </div>

      {/* Operational Safeguards Card */}
      <Card className="bg-slate-50/70 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800">
        <div className="flex items-start space-x-3">
          <ShieldCheckIcon className="w-5 h-5 text-emerald-600 dark:text-emerald-400 mt-0.5 shrink-0" />
          <div className="space-y-1 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            <h3 className="font-semibold text-slate-900 dark:text-white text-sm">
              Operational Security & Data Privacy Assurance
            </h3>
            <p>
              In compliance with production-grade data hygiene standards, CareerPulse strictly prevents the exposure of database credentials, authentication keys, internal VPC subnets, or connection strings. All metrics displayed above originate directly from non-sensitive operational telemetry routes (<code>/health</code>, <code>/metrics</code>, <code>/version</code>).
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
