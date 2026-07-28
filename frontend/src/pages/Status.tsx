import Heading from "../components/common/Heading";
import Card from "../components/common/Card";

export default function Status() {
  return (
    <div className="space-y-6">
      <Heading
        title="System Status"
        subtitle="Data loading freshness indicators and API synchronization lags."
      />
      <Card title="Database Telemetry status" subtitle="Freshness indicators">
        <div className="h-64 flex items-center justify-center text-slate-400 dark:text-slate-600 text-sm">
          System latency monitors and refresh logs table will be rendered here.
        </div>
      </Card>
    </div>
  );
}
