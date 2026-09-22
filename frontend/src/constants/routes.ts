export const ROUTES = {
  DASHBOARD: "/dashboard",
  COMPANIES: "/companies",
  SKILLS: "/skills",
  TECHNOLOGY: "/technology",
  GEOGRAPHY: "/geography",
  SALARY: "/salary",
  STATUS: "/status",
  ABOUT: "/about",
} as const;

export type RoutePath = typeof ROUTES[keyof typeof ROUTES];
export default ROUTES;
