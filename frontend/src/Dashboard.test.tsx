import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { apiClient } from "./api/axios";
import Dashboard from "./pages/Dashboard";
import {
  formatNumber,
  formatCurrency,
  formatPercent,
  formatDate,
  calculatePercentage,
  truncateText,
} from "./utils/formatters";

// Hoisted Recharts mock
vi.mock("recharts", async () => {
  const original = await vi.importActual("recharts");
  return {
    ...original,
    ResponsiveContainer: ({ children }: any) => (
      <div style={{ width: 800, height: 300 }}>{children}</div>
    ),
  };
});

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

const renderDashboard = (queryClient = createTestQueryClient()) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const mockSummary = {
  success: true,
  data: {
    total_jobs: 99,
    total_companies: 93,
    total_locations: 58,
    remote_jobs: 8,
    remote_percentage: 8.08,
    average_salary: 161966.64,
    median_salary: 120000.0,
    highest_salary: 750000.0,
    highest_paying_company: "Interaction Design Foundation",
    top_company: "Growth Org",
    top_skill: "TypeScript",
    top_country: "United States",
    jobs_with_salary: 14,
    jobs_without_salary: 85,
    generation_timestamp: "2026-09-19T10:28:48Z",
  },
};

const mockCompanies = {
  success: true,
  data: [
    { company: "Growth Org", total_jobs: 6, unique_locations: 1 },
    { company: "Design Labs", total_jobs: 3, unique_locations: 2 },
  ],
};

const mockSkills = {
  success: true,
  data: [
    { tag: "TypeScript", job_demand_count: 69 },
    { tag: "React", job_demand_count: 45 },
  ],
};

const mockTechnology = {
  success: true,
  data: [
    { tech_tag: "PostgreSQL", job_demand_count: 50 },
    { tech_tag: "Docker", job_demand_count: 38 },
  ],
};

const mockGeography = {
  success: true,
  data: [
    { country: "United States", region: "California", jobs_count: 32 },
    { country: "Germany", region: "Berlin", jobs_count: 12 },
  ],
};

const mockSalary = {
  success: true,
  data: [
    { salary_tier: "Entry (< 50k)", jobs_count: 3 },
    { salary_tier: "Mid (50k-100k)", jobs_count: 2 },
    { salary_tier: "Senior (100k-150k)", jobs_count: 3 },
    { salary_tier: "Staff (> 150k)", jobs_count: 6 },
  ],
};

const mockHealth = {
  success: true,
  data: { status: "healthy", database: "connected" },
};

describe("Sprint 8.2 — Formatting Helpers Unit Tests", () => {
  it("formats numbers with commas and handles nulls", () => {
    expect(formatNumber(99)).toBe("99");
    expect(formatNumber(15420)).toBe("15,420");
    expect(formatNumber(0)).toBe("0");
    expect(formatNumber(null)).toBe("—");
    expect(formatNumber(undefined)).toBe("—");
  });

  it("formats annual currency and compact formats", () => {
    expect(formatCurrency(161966.64)).toBe("$161,967");
    expect(formatCurrency(750000)).toBe("$750,000");
    expect(formatCurrency(250000, true)).toBe("$250k");
    expect(formatCurrency(1500000, true)).toBe("$1.5M");
    expect(formatCurrency(null)).toBe("—");
  });

  it("formats percentages without excessive precision", () => {
    expect(formatPercent(8.0808)).toBe("8.1%");
    expect(formatPercent(35.5)).toBe("35.5%");
    expect(formatPercent("35.5%")).toBe("35.5%");
    expect(formatPercent(0)).toBe("0%");
    expect(formatPercent(null)).toBe("—");
  });

  it("calculates percentage correctly avoiding divide-by-zero", () => {
    expect(calculatePercentage(14, 99)).toBe("14.1%");
    expect(calculatePercentage(3, 14)).toBe("21.4%");
    expect(calculatePercentage(0, 0)).toBe("0%");
    expect(calculatePercentage(0, 100)).toBe("0%");
  });

  it("formats ISO timestamps into human-readable strings", () => {
    const formatted = formatDate("2026-09-19T10:28:48Z");
    expect(formatted).not.toBe("—");
    expect(formatted).toContain("2026");
    expect(formatDate(null)).toBe("—");
  });

  it("truncates long text gracefully", () => {
    expect(truncateText("Interaction Design Foundation", 16)).toBe("Interaction D...");
    expect(truncateText("Short Text", 16)).toBe("Short Text");
    expect(truncateText("", 16)).toBe("");
  });
});

describe("Sprint 8.2 — Executive Analytics Dashboard Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all 7 KPI cards with formatted live data", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/companies")) return Promise.resolve({ data: mockCompanies });
      if (url.includes("/api/v1/skills")) return Promise.resolve({ data: mockSkills });
      if (url.includes("/api/v1/technology")) return Promise.resolve({ data: mockTechnology });
      if (url.includes("/api/v1/geography")) return Promise.resolve({ data: mockGeography });
      if (url.includes("/api/v1/salary")) return Promise.resolve({ data: mockSalary });
      if (url === "/health") return Promise.resolve({ data: mockHealth });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderDashboard();

    await waitFor(() => {
      const kpiSection = screen.getByLabelText("Key Performance Indicators");
      expect(within(kpiSection).getByText("Total Jobs")).toBeDefined();
      expect(within(kpiSection).getByText("Companies")).toBeDefined();
      expect(within(kpiSection).getByText("Locations")).toBeDefined();
      expect(within(kpiSection).getByText("Remote Jobs")).toBeDefined();
      expect(within(kpiSection).getByText("Remote %")).toBeDefined();
      expect(within(kpiSection).getByText("Jobs With Salary")).toBeDefined();
      expect(within(kpiSection).getByText("Jobs Without Salary")).toBeDefined();

      // Check values inside KPI section
      expect(within(kpiSection).getByText("99")).toBeDefined();
      expect(within(kpiSection).getByText("93")).toBeDefined();
      expect(within(kpiSection).getByText("58")).toBeDefined();
      expect(within(kpiSection).getByText("8")).toBeDefined();
      expect(within(kpiSection).getByText("8.1%")).toBeDefined();
      expect(within(kpiSection).getByText("14")).toBeDefined();
      expect(within(kpiSection).getByText("85")).toBeDefined();
    });
  });

  it("renders all 4 Market Highlights with peak salary", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url === "/health") return Promise.resolve({ data: mockHealth });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Top Company")).toBeDefined();
      expect(screen.getByText("Growth Org")).toBeDefined();

      expect(screen.getByText("Top Skill")).toBeDefined();
      expect(screen.getByText("TypeScript")).toBeDefined();

      expect(screen.getByText("Top Country")).toBeDefined();
      expect(screen.getByText("United States")).toBeDefined();

      expect(screen.getByText("Highest Paying Company")).toBeDefined();
      expect(screen.getByText("Interaction Design Foundation")).toBeDefined();
      expect(screen.getByText("Peak: $750,000")).toBeDefined();
    });
  });

  it("renders individual chart loading skeletons independently", () => {
    // Hang all queries in pending state
    vi.spyOn(apiClient, "get").mockImplementation(() => new Promise(() => {}));

    renderDashboard();

    const pulseElements = document.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it("produces section-level error state when a secondary endpoint fails without breaking the dashboard", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      // Companies endpoint fails
      if (url.includes("/api/v1/companies")) return Promise.reject(new Error("Companies service timed out"));
      if (url.includes("/api/v1/skills")) return Promise.resolve({ data: mockSkills });
      if (url.includes("/api/v1/technology")) return Promise.resolve({ data: mockTechnology });
      if (url.includes("/api/v1/geography")) return Promise.resolve({ data: mockGeography });
      if (url.includes("/api/v1/salary")) return Promise.resolve({ data: mockSalary });
      if (url === "/health") return Promise.resolve({ data: mockHealth });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderDashboard();

    // The rest of the dashboard still loads
    await waitFor(() => {
      expect(screen.getByText("Total Jobs")).toBeDefined();
      expect(screen.getByText("Top In-Demand Skills")).toBeDefined();
    });

    // Section error is displayed for companies
    await waitFor(() => {
      expect(screen.getByText("Failed to load company rankings.")).toBeDefined();
    });
  });

  it("renders empty state message gracefully when data array is empty", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/companies")) return Promise.resolve({ data: { success: true, data: [] } });
      if (url === "/health") return Promise.resolve({ data: mockHealth });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("No company hiring records available.")).toBeDefined();
    });
  });

  it("triggers query refetch when Refresh button is clicked", async () => {
    let callCount = 0;
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") {
        callCount++;
        return Promise.resolve({ data: mockSummary });
      }
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderDashboard();

    const refreshBtn = (await screen.findByRole("button", { name: /refresh/i })) as HTMLButtonElement;
    await waitFor(() => {
      expect(refreshBtn.disabled).toBe(false);
    });

    fireEvent.click(refreshBtn);

    await waitFor(() => {
      expect(callCount).toBeGreaterThan(1);
    });
  });

  it("calculates salary tier breakdown with disclosed, undisclosed, and median figures", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/salary")) return Promise.resolve({ data: mockSalary });
      if (url === "/health") return Promise.resolve({ data: mockHealth });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Disclosed Salary Distribution")).toBeDefined();
      expect(screen.getByText("Disclosed")).toBeDefined();
      expect(screen.getByText("Undisclosed")).toBeDefined();
      expect(screen.getByText("Median")).toBeDefined();
      expect(screen.getByText("$120,000")).toBeDefined();
    });
  });
});
