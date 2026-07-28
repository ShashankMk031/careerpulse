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

      {/* Sidebar aside Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col w-64 bg-slate-900 text-slate-400 border-r border-slate-800 transition-transform duration-200 transform lg:translate-x-0 lg:static lg:z-auto ${
          isOpen ? "translate-x-0" : "-translate-x-0 -translate-x-64"
        }`}
        aria-label="Sidebar Navigation"
      >
        {/* Brand header */}
        <div className="flex items-center justify-between h-16 px-6 bg-slate-950 border-b border-slate-800/80">
          <div className="flex items-center space-x-2.5">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-600 text-white font-bold text-lg shadow-sm">
              C
            </div>
            <span className="text-base font-bold text-white tracking-wide">
              CareerPulse
            </span>
          </div>
          
          {/* Mobile Close Button */}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-450 hover:bg-slate-800 lg:hidden focus:outline-none focus:ring-2 focus:ring-slate-500"
            aria-label="Close sidebar menu"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Navigation Area */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center px-4 py-2.5 text-sm font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-xs"
                      : "hover:bg-slate-800/60 hover:text-slate-205"
                  }`
                }
              >
                <Icon className="w-5 h-5 mr-3 shrink-0" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        {/* User context footer */}
        <div className="p-4 bg-slate-950/40 border-t border-slate-800/60 text-center">
          <p className="text-[10px] uppercase font-semibold tracking-wider text-slate-500">
            System Operational
          </p>
        </div>
      </aside>
    </>
  );
}
