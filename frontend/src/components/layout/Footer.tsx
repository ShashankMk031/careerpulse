
export default function Footer() {
  return (
    <footer className="py-4 px-6 border-t border-slate-100 dark:border-slate-800/40 bg-white dark:bg-slate-900 text-slate-400 dark:text-slate-550 text-xs mt-auto transition-colors duration-150">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 max-w-full">
        <div>
          <span className="font-semibold text-slate-700 dark:text-slate-350">
            CareerPulse Analytics Platform
          </span>{" "}
          • v1.0.0
        </div>
        
        {/* Resource Links */}
        <div className="flex items-center space-x-5">
          <a
            href="https://github.com/ShashankMk031/careerpulse"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors focus:outline-none focus:underline"
          >
            GitHub
          </a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors focus:outline-none focus:underline"
          >
            API Docs
          </a>
        </div>
      </div>
    </footer>
  );
}
export { Footer };
