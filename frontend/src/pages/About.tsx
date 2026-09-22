import {
  CircleStackIcon,
  CloudIcon,
  ServerIcon,
  ComputerDesktopIcon,
  ShieldExclamationIcon,
} from "@heroicons/react/24/outline";

// UI Components
import PageHeader from "../components/common/PageHeader";
import Card from "../components/common/Card";

export default function About() {
  const pipelineSteps = [
    {
      name: "RemoteOK API",
      type: "External Source",
      desc: "Upstream HTTP source providing remote job postings across technology and creative roles.",
      icon: CloudIcon,
      color: "border-sky-300 dark:border-sky-800 bg-sky-50 dark:bg-sky-950/30 text-sky-700 dark:text-sky-300",
    },
    {
      name: "Python Ingestion",
      type: "Batch Ingestor",
      desc: "Scheduled fetcher with request throttling, error resilience, and automated S3 Bronze ingestion.",
      icon: ServerIcon,
      color: "border-indigo-300 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300",
    },
    {
      name: "S3 Bronze Layer",
      type: "Raw Storage",
      desc: "Immutable raw JSON payloads partitioned by date (e.g. s3://.../bronze/source=remoteok/year=2026/...).",
      icon: CircleStackIcon,
      color: "border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-300",
    },
    {
      name: "AWS Glue & S3 Silver",
      type: "Cleansing & Dedup",
      desc: "PySpark ETL cleaning text, enforcing schema, deduplicating IDs, and writing columnar Snappy Parquet.",
      icon: ServerIcon,
      color: "border-purple-300 dark:border-purple-800 bg-purple-50 dark:bg-purple-950/30 text-purple-700 dark:text-purple-300",
    },
    {
      name: "AWS Glue & S3 Gold",
      type: "Analytics Aggregates",
      desc: "Dimensional aggregations for companies, skills, geography, salary tiers, and hiring summary metrics.",
      icon: CircleStackIcon,
      color: "border-yellow-300 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-950/30 text-yellow-700 dark:text-yellow-300",
    },
    {
      name: "Amazon RDS PostgreSQL",
      type: "Serving Layer",
      desc: "Relational database with connection pooling, indexes, views, and load metadata tracking.",
      icon: CircleStackIcon,
      color: "border-emerald-300 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300",
    },
    {
      name: "FastAPI REST Service",
      type: "API Layer",
      desc: "High-performance Python API with database timing headers (X-Database-Time-MS) and pydantic models.",
      icon: ServerIcon,
      color: "border-cyan-300 dark:border-cyan-800 bg-cyan-50 dark:bg-cyan-950/30 text-cyan-700 dark:text-cyan-300",
    },
    {
      name: "React + Vite Dashboard",
      type: "Presentation Tier",
      desc: "Modern responsive frontend with TanStack Query caching, Recharts visualizations, and dark mode.",
      icon: ComputerDesktopIcon,
      color: "border-violet-300 dark:border-violet-800 bg-violet-50 dark:bg-violet-950/30 text-violet-700 dark:text-violet-300",
    },
  ];

  const techStack = [
    { layer: "Cloud Infrastructure", tech: "AWS (S3, Glue, Athena, RDS PostgreSQL, VPC, Security Groups)" },
    { layer: "Data Processing", tech: "Apache Spark / AWS Glue PySpark, Snappy Parquet, Glue Job Bookmarks" },
    { layer: "Serving Database", tech: "PostgreSQL on Amazon RDS (serving_db.serving schema)" },
    { layer: "Backend Service", tech: "FastAPI, Python 3.12, psycopg2-binary, ThreadedConnectionPool, Pydantic V2" },
    { layer: "Frontend Framework", tech: "React 19, TypeScript, Vite, Tailwind CSS" },
    { layer: "State & Data Fetching", tech: "TanStack Query (React Query v5), Axios" },
    { layer: "Data Visualization", tech: "Recharts (Responsive horizontal bar charts)" },
    { layer: "Icons & UI", tech: "Heroicons, Custom design tokens" },
  ];

  return (
    <div className="space-y-8 max-w-5xl">
      <PageHeader
        title="About CareerPulse"
        subtitle="Architecture, data pipelines, technical implementation, and analytical methodology."
      />

      {/* 1. What is CareerPulse? */}
      <Card title="1. What is CareerPulse?" subtitle="Mission and core value proposition">
        <div className="text-sm text-slate-600 dark:text-slate-300 space-y-3 leading-relaxed">
          <p>
            <strong>CareerPulse</strong> is an end-to-end cloud-native job market intelligence platform built to monitor, extract, and analyze the dynamics of the global remote employment landscape.
          </p>
          <p>
            By combining a multi-tier AWS data lakehouse (Bronze, Silver, Gold) with an operational PostgreSQL serving layer and a real-time React analytics interface, CareerPulse answers critical labor market questions: Which technical competencies command the highest market frequency? Which organizations are actively hiring? What does the salary transparency landscape look like?
          </p>
        </div>
      </Card>

      {/* 2. Architecture & Interactive Diagram */}
      <Card title="2. Architecture Flow Diagram" subtitle="End-to-end data trajectory from web ingestion to interactive dashboard">
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {pipelineSteps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.name}
                  className={`p-4 rounded-xl border ${step.color} transition-all duration-200 hover:shadow-xs flex flex-col justify-between`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-white/70 dark:bg-black/30">
                        Step {idx + 1}
                      </span>
                      <Icon className="w-5 h-5 opacity-80" />
                    </div>
                    <h2 className="font-bold text-slate-900 dark:text-white text-sm">
                      {step.name}
                    </h2>
                    <div className="text-[11px] font-medium opacity-75 mb-2">
                      {step.type}
                    </div>
                    <p className="text-xs opacity-90 leading-snug">
                      {step.desc}
                    </p>
                  </div>
                  {idx < pipelineSteps.length - 1 && (
                    <div className="hidden lg:flex justify-end pt-3">
                      <span className="text-xs font-mono opacity-50">→</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      {/* 3. Data Pipeline & Lakehouse */}
      <Card title="3. Data Pipeline & Lakehouse Architecture" subtitle="Multi-hop medallion architecture (Bronze → Silver → Gold)">
        <div className="space-y-4 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
          <div className="border-l-2 border-amber-500 pl-3.5 space-y-1">
            <h2 className="font-semibold text-slate-900 dark:text-white text-sm">Bronze Tier (Raw Ingestion)</h2>
            <p>
              Extracts unprocessed payload batches from RemoteOK and persists them in raw JSON within <code>s3://.../bronze/</code>. Data remains strictly immutable to ensure exact replayability.
            </p>
          </div>
          <div className="border-l-2 border-purple-500 pl-3.5 space-y-1">
            <h2 className="font-semibold text-slate-900 dark:text-white text-sm">Silver Tier (Cleaned & Deduplicated)</h2>
            <p>
              AWS Glue PySpark jobs parse timestamps, strip HTML, normalize salary boundaries, and eliminate duplicates based on unique posting IDs. Parquet files with Snappy compression are written with Glue catalog partitioning.
            </p>
          </div>
          <div className="border-l-2 border-yellow-500 pl-3.5 space-y-1">
            <h2 className="font-semibold text-slate-900 dark:text-white text-sm">Gold Tier (Analytics Aggregations)</h2>
            <p>
              Pre-aggregates six core business views: <code>gold_summary</code>, <code>gold_company</code>, <code>gold_skills</code>, <code>gold_technology</code>, <code>gold_geography</code>, and <code>gold_salary</code>, ensuring O(1) read performance for subsequent queries.
            </p>
          </div>
        </div>
      </Card>

      {/* 4. Serving Layer & API */}
      <Card title="4. Serving Layer & API Architecture" subtitle="Sub-millisecond relational serving with ThreadedConnectionPool">
        <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
          <p>
            The serving layer resides in an Amazon RDS PostgreSQL instance within the <code>serving_db.serving</code> schema. The backend service is built on <strong>FastAPI</strong>, utilizing a thread-safe connection pool (<code>ThreadedConnectionPool(minconn=2, maxconn=10)</code>) to handle high-throughput concurrent requests without connection leakage.
          </p>
          <p>
            Custom middleware injects real-time performance tracking headers into every response:
          </p>
          <ul className="list-disc pl-5 space-y-1 font-mono text-[11px]">
            <li><code>X-Request-ID</code>: Unique UUIDv4 transaction correlation identifier</li>
            <li><code>X-Process-Time-MS</code>: Total elapsed request lifecycle duration</li>
            <li><code>X-Database-Time-MS</code>: Exact accumulated PostgreSQL repository execution time</li>
          </ul>
        </div>
      </Card>

      {/* 5. Technology Stack Table */}
      <Card title="5. Complete Technology Stack" subtitle="Production-grade tools and libraries utilized across the platform">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850 text-slate-500 dark:text-slate-400 uppercase font-semibold">
                <th className="px-4 py-2.5">Platform Layer</th>
                <th className="px-4 py-2.5">Technology & Architecture Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
              {techStack.map((item) => (
                <tr key={item.layer} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/40">
                  <td className="px-4 py-2.5 font-semibold text-slate-900 dark:text-white whitespace-nowrap">
                    {item.layer}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-slate-600 dark:text-slate-400">
                    {item.tech}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* 6. Data Semantics & Limitations */}
      <Card className="border-amber-200/80 dark:border-amber-900/50 bg-amber-50/40 dark:bg-amber-950/20">
        <div className="flex items-start space-x-3">
          <ShieldExclamationIcon className="w-6 h-6 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-2 text-xs text-amber-900 dark:text-amber-200 leading-relaxed">
            <h2 className="font-bold text-sm text-amber-900 dark:text-amber-100">
              6. Data Semantics & Analytical Limitations
            </h2>
            <p>
              <strong>Important Scope Limitation:</strong> CareerPulse currently analyzes the available RemoteOK snapshot. It should not be interpreted as a complete representation of the entire remote-job market.
            </p>
            <p>
              <strong>Snapshot vs. Cumulative Dimensions:</strong>
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li>
                <strong>Current Snapshot:</strong> The hiring summary reflects the latest processed snapshot of <strong>99 deduplicated jobs</strong> (93 active companies, 14 disclosed salaries, 8 remote designations).
              </li>
              <li>
                <strong>Cumulative Dimensions:</strong> Dimension tables (companies, skills, technology, geography) maintain historical records (e.g. 175 companies, 126 skills) across continuous ingestion runs. Cumulative figures should not be conflated with single-day snapshot metrics.
              </li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}
