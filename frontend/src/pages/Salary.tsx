import Heading from "../components/common/Heading";
import Card from "../components/common/Card";

export default function Salary() {
  return (
    <div className="space-y-6">
      <Heading
        title="Salary Distribution"
        subtitle="Hiring volume segments by salary ranges and brackets."
      />
      <Card title="Salary Tier Breakdowns" subtitle="Income brackets distribution">
        <div className="h-64 flex items-center justify-center text-slate-400 dark:text-slate-600 text-sm">
          Salary histogram metrics and tables will be rendered here.
        </div>
      </Card>
    </div>
  );
}
