import Heading from "../components/common/Heading";
import Card from "../components/common/Card";

export default function Geography() {
  return (
    <div className="space-y-6">
      <Heading
        title="Geography & Markets"
        subtitle="Global job densities and country-level breakdowns."
      />
      <Card title="Regional Distribution" subtitle="Hiring concentrations">
        <div className="h-64 flex items-center justify-center text-slate-400 dark:text-slate-600 text-sm">
          Geographic concentration maps and lists will be rendered here.
        </div>
      </Card>
    </div>
  );
}
