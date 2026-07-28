import Heading from "../components/common/Heading";
import Card from "../components/common/Card";

export default function Skills() {
  return (
    <div className="space-y-6">
      <Heading
        title="Skills & Talents"
        subtitle="Skill tag demand analysis and average starting premiums."
      />
      <Card title="Market Skill Demand" subtitle="Keyword concentration">
        <div className="h-64 flex items-center justify-center text-slate-400 dark:text-slate-600 text-sm">
          Skills list and tag cloud charts will be rendered here.
        </div>
      </Card>
    </div>
  );
}
