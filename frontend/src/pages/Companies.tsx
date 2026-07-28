import Heading from "../components/common/Heading";
import Card from "../components/common/Card";

export default function Companies() {
  return (
    <div className="space-y-6">
      <Heading
        title="Companies Analytics"
        subtitle="Hiring volume summaries and top paying organisations."
      />
      <Card title="Active Hiring Companies" subtitle="Organizational breakdown">
        <div className="h-64 flex items-center justify-center text-slate-400 dark:text-slate-600 text-sm">
          Active companies table and sorting indicators will be rendered here.
        </div>
      </Card>
    </div>
  );
}
