import Heading from "../components/common/Heading";
import Card from "../components/common/Card";

export default function About() {
  return (
    <div className="space-y-6">
      <Heading
        title="About CareerPulse"
        subtitle="Operational architecture, metadata versions, and team guides."
      />
      <Card title="Analytics Platform Details" subtitle="Version 1.0.0">
        <div className="space-y-4 max-w-2xl text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
          <p>
            CareerPulse is a production-ready, data-driven job market intelligence platform.
            The backend pipeline fetches raw job advertisements, processes them using structured Spark workloads,
            normalizes entities inside database schemas, and displays serving-layer analytics via a performant FastAPI REST service.
          </p>
          <p>
            This frontend acts as the control panel, pulling real-time aggregate charts, country distributions,
            skills demand rankings, and tech stack configurations to provide stakeholders with actionable talent insights.
          </p>
        </div>
      </Card>
    </div>
  );
}
