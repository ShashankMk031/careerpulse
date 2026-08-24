import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { apiClient } from "./api/axios";
import { API_BASE_URL } from "./config/env";
import { AppRoutes } from "./App";
import Sidebar from "./components/layout/Sidebar";
import ThemeToggle from "./components/common/ThemeToggle";
import { THEME_KEY, THEMES } from "./constants/theme";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

const renderWithProviders = (ui: React.ReactElement, queryClient = createTestQueryClient()) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
};

const mockSummary = {
  success: true,
  data: {
    total_jobs: 15420,
    total_companies: 840,
    total_locations: 12,
    remote_percentage: 35.5,
    jobs_with_salary: 5400,
    jobs_without_salary: 10020,
    top_company: "Google Corp",
    top_skill: "Python Lang",
    generation_timestamp: "2026-07-28T12:00:00Z",
  },
};

const mockCompanies = {
  success: true,
  data: [
    { company: "Google Corp", total_jobs: 120, avg_salary_min: 120000, avg_salary_max: 180000 },
    { company: "Meta", total_jobs: 95, avg_salary_min: 130000, avg_salary_max: 190000 },
  ],
};

const mockSkills = {
  success: true,
  data: [
    { tag: "Python Lang", job_demand_count: 320, avg_salary_min: 110000, avg_salary_max: 160000 },
    { tag: "React", job_demand_count: 240, avg_salary_min: 100000, avg_salary_max: 140000 },
  ],
};

const mockTechnology = {
  success: true,
  data: [
    { tech_tag: "PostgreSQL", job_demand_count: 450, avg_salary_min: 105000, avg_salary_max: 150000 },
  ],
};

const mockGeography = {
  success: true,
  data: [
    { country: "United States", region: "California", jobs_count: 850, avg_salary_min: 125000 },
  ],
};

const mockSalary = {
  success: true,
  data: [
    { salary_tier: "100k-150k", jobs_count: 3400 },
  ],
};

const mockFreshness = {
  success: true,
  data: [
    { dataset: "jobs_loading", last_refresh: "2026-07-28T11:00:00Z", current_age: "1h 48m ago", refresh_lag_minutes: 108, status: "Fresh" },
  ],
};

const mockHealth = {
  success: true,
  data: { status: "healthy", database: "connected" },
};

const mockVersion = {
  success: true,
  data: { version: "1.2.3", git_commit: "05240062f8319f6a7d1887eefcbdf742ec8ac670", build_timestamp: "2026-07-25T18:17:00Z" },
};

describe("Frontend Dashboard & Analytics Tests", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
    vi.clearAllMocks();

    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    vi.mock("recharts", async () => {
      const original = await vi.importActual("recharts");
      return {
        ...original,
        ResponsiveContainer: ({ children }: any) => (
          <div style={{ width: 800, height: 300 }}>{children}</div>
        ),
      };
    });
  });

  describe("API Client Configurations", () => {
    it("should resolve the expected backend base URL from env overrides", () => {
      expect(apiClient.defaults.baseURL).toBe(API_BASE_URL);
    });
  });

  describe("Theme Manager Persistence", () => {
    it("should toggle theme classes and write configurations to localStorage", () => {
      render(<ThemeToggle />);
      const button = screen.getByRole("button");

      fireEvent.click(button);
      expect(localStorage.getItem(THEME_KEY)).toBe(THEMES.DARK);
      expect(document.documentElement.classList.contains("dark")).toBe(true);

      fireEvent.click(button);
      expect(localStorage.getItem(THEME_KEY)).toBe(THEMES.LIGHT);
      expect(document.documentElement.classList.contains("dark")).toBe(false);
    });
  });

  describe("SaaS Navigation Drawer Links", () => {
    it("should render side navigation menu options", () => {
      renderWithProviders(<Sidebar isOpen={true} onClose={() => {}} />);
      expect(screen.getByText("Dashboard")).toBeDefined();
      expect(screen.getByText("Companies")).toBeDefined();
      expect(screen.getByText("System Status")).toBeDefined();
    });
  });

  describe("Executive Dashboard Render Pipeline", () => {
    it("should display loading skeletons during active API request hooks", () => {
      vi.spyOn(apiClient, "get").mockImplementation(() => new Promise(() => {}));

      renderWithProviders(<AppRoutes />);

      const skeletons = document.querySelectorAll(".animate-pulse");
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it("should render visual ErrorState panel if database query connection fails", async () => {
      vi.spyOn(apiClient, "get").mockRejectedValue(new Error("Database connection down"));

      renderWithProviders(<AppRoutes />);

      await waitFor(() => {
        expect(screen.getByText("Dashboard System Error")).toBeDefined();
        expect(screen.getByText("Try Again")).toBeDefined();
      });
    });

    it("should render full visual layout metrics, cards, and Recharts once API loads", async () => {
      vi.spyOn(apiClient, "get").mockImplementation((url) => {
        if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
        if (url.includes("/api/v1/companies")) return Promise.resolve({ data: mockCompanies });
        if (url.includes("/api/v1/skills")) return Promise.resolve({ data: mockSkills });
        if (url.includes("/api/v1/technology")) return Promise.resolve({ data: mockTechnology });
        if (url.includes("/api/v1/geography")) return Promise.resolve({ data: mockGeography });
        if (url.includes("/api/v1/salary")) return Promise.resolve({ data: mockSalary });
        if (url === "/metrics") return Promise.resolve({ data: mockFreshness });
        if (url === "/health") return Promise.resolve({ data: mockHealth });
        if (url === "/version") return Promise.resolve({ data: mockVersion });
        return Promise.reject(new Error(`Unhandled URL: ${url}`));
      });

      renderWithProviders(<AppRoutes />);

      await waitFor(() => {
        expect(screen.getByText("15,420")).toBeDefined();
        expect(screen.getByText("840")).toBeDefined();
        expect(screen.getByText("35.5%")).toBeDefined();
        expect(screen.getByText("Google Corp")).toBeDefined();
        expect(screen.getByText("Python Lang")).toBeDefined();
      });

      expect(screen.getByText("jobs_loading")).toBeDefined();
      expect(screen.getByText("1.2.3")).toBeDefined();
      expect(screen.getByText("0524006")).toBeDefined();
    });
  });

  describe("Companies Page Interactions", () => {
    it("should allow search filtering and pagination", async () => {
      let requestedParams: any = null;
      vi.spyOn(apiClient, "get").mockImplementation((url, config) => {
        if (url.includes("/api/v1/companies")) {
          requestedParams = config?.params;
          return Promise.resolve({
            data: {
              success: true,
              data: [
                { company: "SearchTarget", total_jobs: 10 }
              ],
              metadata: {
                page: 1,
                page_size: 20,
                total_records: 1,
                total_pages: 1,
                has_next: false,
                has_previous: false
              }
            }
          });
        }
        if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
        return Promise.resolve({ data: { success: true, data: [] } });
      });

      render(
        <QueryClientProvider client={createTestQueryClient()}>
          <MemoryRouter initialEntries={["/companies"]}>
            <AppRoutes />
          </MemoryRouter>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByPlaceholderText("Search companies...")).toBeDefined();
      });

      const searchInput = screen.getByPlaceholderText("Search companies...");
      fireEvent.change(searchInput, { target: { value: "Google" } });

      await waitFor(() => {
        expect(screen.getByText("SearchTarget")).toBeDefined();
        expect(requestedParams?.search).toBe("Google");
      });
    });
  });
});
