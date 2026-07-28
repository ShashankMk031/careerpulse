export const THEME_KEY = "careerpulse_theme";
export const THEMES = {
  LIGHT: "light",
  DARK: "dark",
} as const;

export type Theme = typeof THEMES[keyof typeof THEMES];
