import { Link } from "react-router-dom";
import { FaceFrownIcon } from "@heroicons/react/24/outline";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[450px] p-6 text-center">
      <div className="flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 mb-6">
        <FaceFrownIcon className="w-10 h-10" />
      </div>
      <h1 className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-2 my-0">
        404
      </h1>
      <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-4 my-0">
        Page Not Found
      </h2>
      <p className="text-sm text-slate-550 dark:text-slate-400 max-w-sm mb-6 leading-relaxed">
        The dashboard view you are trying to reach does not exist or has been relocated.
      </p>
      <Link
        to="/"
        className="px-5 py-2.5 text-sm font-medium text-white bg-indigo-650 rounded-lg hover:bg-indigo-750 active:bg-indigo-800 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-slate-950"
      >
        Return to Dashboard
      </Link>
    </div>
  );
}
export { NotFound };
