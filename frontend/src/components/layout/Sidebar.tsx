import { NavLink } from "react-router-dom";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { NAV_ITEMS } from "../../config/navigation";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-xs lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Aside Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col w-64 bg-slate-900 text-slate-400 border-r border-slate-800 transition-transform duration-200 transform lg:translate-x-0 lg:static lg:z-auto ${
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
        aria-label="Sidebar Navigation"
      >
        {/* Brand header */}
        <div className="flex items-center justify-between h-16 px-5 bg-slate-950 border-b border-slate-800/80">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-600 text-white font-bold text-lg shadow-sm">
              C
            </div>
            <div>
              <div className="text-sm font-bold text-white tracking-tight leading-none">
                CareerPulse
              </div>
              <div className="text-[10px] text-slate-400 leading-tight mt-1 truncate">
                Cloud Job Market Intelligence
              </div>
            </div>
          </div>

          {/* Mobile Close Button */}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 lg:hidden focus:outline-none focus:ring-2 focus:ring-slate-500 cursor-pointer"
            aria-label="Close sidebar menu"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Navigation Area */}
        <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center px-3.5 py-2.5 text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-xs"
                      : "text-slate-400 hover:bg-slate-800/70 hover:text-slate-200"
                  }`
                }
              >
                <Icon className="w-5 h-5 mr-3 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Footer info */}
        <div className="p-4 bg-slate-950/60 border-t border-slate-800/80">
          <div className="flex items-center justify-between text-[11px] text-slate-500">
            <span>CareerPulse v1.0.0</span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Serving Live
            </span>
          </div>
        </div>
      </aside>
    </>
  );
}

export { Sidebar };
