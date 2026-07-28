import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export default function ErrorState({
  title = "Error Loading Data",
  message = "We encountered a problem while pulling the requested analytics metrics. Please check your network connection.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-red-50/50 dark:bg-red-950/10 border border-red-100 dark:border-red-950/20 rounded-xl max-w-lg mx-auto my-6">
      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-100 dark:bg-red-950/40 text-red-600 dark:text-red-400 mb-4">
        <ExclamationTriangleIcon className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-semibold text-red-800 dark:text-red-400 mb-2">
        {title}
      </h3>
      <p className="text-sm text-red-700/80 dark:text-red-300/80 mb-5 leading-relaxed max-w-sm">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          type="button"
          className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 active:bg-red-800 transition-colors focus:outline-none focus:ring-2 focus:ring-red-550 focus:ring-offset-2 dark:focus:ring-offset-slate-950"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
