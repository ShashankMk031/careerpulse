import { useEffect, useState } from "react";
import { SunIcon, MoonIcon } from "@heroicons/react/24/outline";
import { THEME_KEY, THEMES, type Theme } from "../../constants/theme";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem(THEME_KEY) as Theme;
    if (saved === THEMES.LIGHT || saved === THEMES.DARK) return saved;
    // Default to system preferences
    if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return THEMES.DARK;
    }
    return THEMES.LIGHT;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === THEMES.DARK) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === THEMES.LIGHT ? THEMES.DARK : THEMES.LIGHT));
  };

  return (
    <button
      onClick={toggleTheme}
      type="button"
      className="p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/80 rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500"
      aria-label={`Switch to ${theme === THEMES.LIGHT ? "dark" : "light"} mode`}
    >
      {theme === THEMES.LIGHT ? (
        <MoonIcon className="w-5 h-5" />
      ) : (
        <SunIcon className="w-5 h-5" />
      )}
    </button>
  );
}
export { ThemeToggle };
