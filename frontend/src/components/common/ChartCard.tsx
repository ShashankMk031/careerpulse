import { type ReactNode } from "react";
import Card from "./Card";
import ErrorState from "./ErrorState";
import EmptyState from "./EmptyState";
import { SkeletonList } from "./Loading";

interface ChartCardProps {
  title: string;
  subtitle?: string;
  loading: boolean;
  error: boolean;
  errorMessage?: string;
  empty: boolean;
  onRetry?: () => void;
  children: ReactNode;
}

export default function ChartCard({
  title,
  subtitle,
  loading,
  error,
  errorMessage,
  empty,
  onRetry,
  children,
}: ChartCardProps) {
  return (
    <Card title={title} subtitle={subtitle}>
      {loading ? (
        <div className="h-[300px] flex flex-col justify-center">
          <SkeletonList rows={3} />
        </div>
      ) : error ? (
        <div className="h-[300px] flex items-center justify-center">
          <ErrorState message={errorMessage} onRetry={onRetry} />
        </div>
      ) : empty ? (
        <div className="h-[300px] flex items-center justify-center">
          <EmptyState />
        </div>
      ) : (
        <div className="h-[300px] w-full">{children}</div>
      )}
    </Card>
  );
}
export { ChartCard };
