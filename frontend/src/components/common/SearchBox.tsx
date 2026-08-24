import { useState, useEffect, type ChangeEvent } from "react";
import { MagnifyingGlassIcon, XMarkIcon } from "@heroicons/react/24/outline";

interface SearchBoxProps {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
}

export default function SearchBox({
  value,
  onChange,
  placeholder = "Search postings...",
}: SearchBoxProps) {
  const [localVal, setLocalVal] = useState(value);

  useEffect(() => {
    setLocalVal(value);
  }, [value]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (localVal !== value) {
        onChange(localVal);
      }
    }, 350);
    return () => clearTimeout(timer);
  }, [localVal, onChange, value]);

  const handleClear = () => {
    setLocalVal("");
    onChange("");
  };

  return (
    <div className="relative w-full max-w-xs">
      <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-450 dark:text-slate-500">
        <MagnifyingGlassIcon className="w-4 h-4" />
      </div>
      <input
        type="text"
        value={localVal}
        onChange={(e: ChangeEvent<HTMLInputElement>) => setLocalVal(e.target.value)}
        placeholder={placeholder}
        aria-label="Search input"
        className="w-full pl-9 pr-8 py-2 border rounded-lg text-sm bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus-visible:ring-2 focus-visible:ring-indigo-500 transition-colors"
      />
      {localVal && (
        <button
          onClick={handleClear}
          type="button"
          className="absolute inset-y-0 right-0 flex items-center pr-2.5 text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-350"
          aria-label="Clear search input"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
export { SearchBox };
