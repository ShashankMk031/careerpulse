import Heading from "../components/common/Heading";
import Card from "../components/common/Card";

export default function Technology() {
  return (
    <div className="space-y-6">
      <Heading
        title="Technology Stacks"
        subtitle="Framework adoption lists and tool demand metrics."
      />
      <Card title="Tech Stack Concentration" subtitle="Engineering demand">
        <div className="h-64 flex items-center justify-center text-slate-400 dark:text-slate-600 text-sm">
          Technology distribution charts and tables will be rendered here.
        </div>
      </Card>
    </div>
  );
}
