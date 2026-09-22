import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { apiClient } from "./api/axios";

// Pages
import Companies from "./pages/Companies";
import Skills from "./pages/Skills";
import Technology from "./pages/Technology";
import Geography from "./pages/Geography";
import Salary from "./pages/Salary";
import Status from "./pages/Status";
import About from "./pages/About";

// Top-level Recharts mock
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

const renderWithProviders = (ui: React.ReactElement, queryClient = createTestQueryClient()) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
};

// Common test fixtures
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
    {
      company: "Interaction Design Foundation",
      total_jobs: 6,
      unique_locations: 2,
      avg_salary_min: 150000,
      avg_salary_max: 750000,
      original_jobs_count: 0,
      highest_paying_role: "Lead Product Designer",
      latest_posting: "2026-09-19T08:12:00Z",
      jobs_with_salary: 2,
    },
    {
      company: "X-Team",
      total_jobs: 4,
      unique_locations: 1,
      avg_salary_min: null,
      avg_salary_max: null,
      original_jobs_count: 0,
      highest_paying_role: null,
      latest_posting: "2026-09-18T14:30:00Z",
      jobs_with_salary: 0,
    },
  ],
  metadata: {
    page: 1,
    page_size: 10,
    total_records: 175,
    total_pages: 18,
    has_next: true,
    has_previous: false,
  },
};

const mockSkills = {
  success: true,
  data: [
    { tag: "exec", job_demand_count: 69, avg_salary_min: 120000, avg_salary_max: 150000, salary_premium: 15000, remote_jobs_count: 5 },
    { tag: "digital nomad", job_demand_count: 58, avg_salary_min: 100000, avg_salary_max: 130000, salary_premium: null, remote_jobs_count: 3 },
  ],
  metadata: {
    page: 1,
    page_size: 10,
    total_records: 126,
    total_pages: 13,
    has_next: true,
    has_previous: false,
  },
};

const mockTechnology = {
  success: true,
  data: [
    { tech_tag: "exec", job_demand_count: 69, avg_salary_min: 120000, avg_salary_max: 150000, top_company: "GROW10X" },
    { tech_tag: "React", job_demand_count: 45, avg_salary_min: 90000, avg_salary_max: 130000, top_company: "Stone" },
  ],
  metadata: {
    page: 1,
    page_size: 10,
    total_records: 126,
    total_pages: 13,
    has_next: true,
    has_previous: false,
  },
};

const mockGeography = {
  success: true,
  data: [
    {
      country: "Unknown",
      region: "onsite",
      jobs_count: 32,
      avg_salary_min: 45457,
      avg_salary_max: 267276,
      company_count: 29,
      remote_count: 0,
      onsite_count: 32,
      hybrid_count: 0,
    },
    {
      country: "Remote",
      region: "Remote",
      jobs_count: 8,
      avg_salary_min: null,
      avg_salary_max: null,
      company_count: 8,
      remote_count: 8,
      onsite_count: 0,
      hybrid_count: 0,
    },
  ],
};

const mockSalary = {
  success: true,
  data: [
    { salary_tier: "Entry (< 50k)", jobs_count: 3, avg_salary_min: 16676, avg_salary_max: 20012 },
    { salary_tier: "Mid (50k-100k)", jobs_count: 3, avg_salary_min: 60000, avg_salary_max: 76666 },
    { salary_tier: "Staff (150k+)", jobs_count: 8, avg_salary_min: 95000, avg_salary_max: 406875 },
    { salary_tier: "Not Specified", jobs_count: 85, avg_salary_min: null, avg_salary_max: null },
  ],
};

const mockHealthHealthy = {
  success: true,
  data: { status: "healthy", database: "connected" },
};

const mockHealthDegraded = {
  success: true,
  data: { status: "degraded", database: "disconnected" },
};

const mockMetrics = {
  success: true,
  data: [
    {
      dataset: "company",
      status: "FRESH",
      refresh_lag_minutes: 15.2,
      current_age: "0 days 00:15:12",
      source_generation_timestamp: "2026-09-19T10:28:38Z",
      last_refresh: "2026-09-19T10:43:50Z",
    },
    {
      dataset: "salary",
      status: "STALE",
      refresh_lag_minutes: 130.5,
      current_age: "1 day 02:10:00",
      source_generation_timestamp: "2026-09-19T10:28:43Z",
      last_refresh: "2026-09-19T12:39:45Z",
    },
  ],
};

const mockVersion = {
  success: true,
  data: {
    version: "1.0.0",
    git_commit: "c0808c017e873ebeb4e3556c5dd4dc1d3c6f5427",
    build_timestamp: "2026-07-25T18:17:00Z",
    python_version: "3.12.9 (main)",
  },
};

describe("Sprint 8.3 — Companies Page (/companies)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("1. renders company data and summary cards", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/companies")) return Promise.resolve({ data: mockCompanies });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Companies />);

    await waitFor(() => {
      expect(screen.getByText("Companies")).toBeDefined();
      expect(screen.getByText("Interaction Design Foundation")).toBeDefined();
      expect(screen.getByText("X-Team")).toBeDefined();
      expect(screen.getByText("175")).toBeDefined(); // Companies represented
    });
  });

  it("2. supports pagination parameters", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/companies")) return Promise.resolve({ data: mockCompanies });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Companies />);

    await waitFor(() => {
      expect(screen.getByText(/Showing page 1 of 18/i)).toBeDefined();
    });
  });

  it("3. handles loading state", () => {
    vi.spyOn(apiClient, "get").mockImplementation(() => new Promise(() => {}));
    renderWithProviders(<Companies />);
    const pulses = document.querySelectorAll(".animate-pulse");
    expect(pulses.length).toBeGreaterThan(0);
  });

  it("4. handles error state with retry", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/companies")) return Promise.reject(new Error("Server offline"));
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Companies />);

    await waitFor(() => {
      expect(screen.getByText("Server offline")).toBeDefined();
    });
  });

  it("5. renders empty state", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/companies")) {
        return Promise.resolve({
          data: {
            success: true,
            data: [],
            metadata: { page: 1, page_size: 10, total_records: 0, total_pages: 0, has_next: false, has_previous: false },
          },
        });
      }
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Companies />);

    await waitFor(() => {
      expect(screen.getByText("No companies found")).toBeDefined();
    });
  });
});

describe("Sprint 8.3 — Skills Page (/skills)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("6. renders skill data and demand metrics", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/skills")) return Promise.resolve({ data: mockSkills });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Skills />);

    await waitFor(() => {
      expect(screen.getByText("Skills Demand")).toBeDefined();
      expect(screen.getByText("exec")).toBeDefined();
      expect(screen.getByText("digital nomad")).toBeDefined();
    });
  });

  it("7. renders ranking and chart components", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/skills")) return Promise.resolve({ data: mockSkills });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Skills />);

    await waitFor(() => {
      expect(screen.getByText("Top 10 In-Demand Skills")).toBeDefined();
      expect(screen.getAllByText(/69 jobs/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it("8. handles skills loading and error states", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/skills")) return Promise.reject(new Error("Skills connection error"));
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Skills />);

    await waitFor(() => {
      expect(screen.getByText("Skills connection error")).toBeDefined();
    });
  });
});

describe("Sprint 8.3 — Technology Page (/technology)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("9. renders technology data and top employer", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url.includes("/api/v1/technology")) return Promise.resolve({ data: mockTechnology });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Technology />);

    await waitFor(() => {
      expect(screen.getByText("Technology & Tooling")).toBeDefined();
      expect(screen.getByText("GROW10X")).toBeDefined();
      expect(screen.getByText("Stone")).toBeDefined();
    });
  });

  it("10. renders top technology bar chart", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url.includes("/api/v1/technology")) return Promise.resolve({ data: mockTechnology });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Technology />);

    await waitFor(() => {
      expect(screen.getByText("Top 10 Technology Demand")).toBeDefined();
    });
  });

  it("11. handles technology error states", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url.includes("/api/v1/technology")) return Promise.reject(new Error("Tech API error"));
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Technology />);

    await waitFor(() => {
      expect(screen.getByText("Tech API error")).toBeDefined();
    });
  });
});

describe("Sprint 8.3 — Geography Page (/geography)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("12. renders geography data and regional density", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/geography")) return Promise.resolve({ data: mockGeography });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Geography />);

    await waitFor(() => {
      expect(screen.getByText("Geographic Distribution")).toBeDefined();
      expect(screen.getByText("Unknown")).toBeDefined();
      expect(screen.getByText("Remote")).toBeDefined();
      expect(screen.getAllByText("32").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("13. displays the mandatory cumulative-data disclaimer notice", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/geography")) return Promise.resolve({ data: mockGeography });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Geography />);

    await waitFor(() => {
      expect(
        screen.getByText(/Geographic distribution is based on the cumulative analytics dimension/i)
      ).toBeDefined();
    });
  });

  it("14. handles geography loading and error states", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url.includes("/api/v1/geography")) return Promise.reject(new Error("Geo service failed"));
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Geography />);

    await waitFor(() => {
      expect(screen.getByText("Geo service failed")).toBeDefined();
    });
  });
});

describe("Sprint 8.3 — Salary Page (/salary)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("15. renders exact API salary tiers without Senior tier", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/salary")) return Promise.resolve({ data: mockSalary });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Salary />);

    await waitFor(() => {
      expect(screen.getByText("Salary Benchmarks")).toBeDefined();
      expect(screen.getByText("Entry (< 50k)")).toBeDefined();
      expect(screen.getByText("Mid (50k-100k)")).toBeDefined();
      expect(screen.getByText("Staff (150k+)")).toBeDefined();
      expect(screen.getAllByText("Not Specified").length).toBeGreaterThanOrEqual(1);

      // Ensure NO Senior tier was fabricated
      expect(screen.queryByText("Senior (100k-150k)")).toBeNull();
    });
  });

  it("16. calculates salary percentages for disclosed jobs", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/salary")) return Promise.resolve({ data: mockSalary });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Salary />);

    await waitFor(() => {
      // 8 / 14 = 57.1%
      expect(screen.getByText("57.1%")).toBeDefined();
    });
  });

  it("17. clearly distinguishes disclosed vs undisclosed jobs", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/salary")) return Promise.resolve({ data: mockSalary });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Salary />);

    await waitFor(() => {
      expect(screen.getAllByText("Disclosed Tier").length).toBe(3);
      expect(screen.getByText("Undisclosed Compensation")).toBeDefined();
    });
  });

  it("18. handles salary loading and error states", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url.includes("/api/v1/salary")) return Promise.reject(new Error("Salary database error"));
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Salary />);

    await waitFor(() => {
      expect(screen.getByText("Salary database error")).toBeDefined();
    });
  });
});

describe("Sprint 8.3 — Status Page (/status)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("19. renders healthy system operational state", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/health") return Promise.resolve({ data: mockHealthHealthy });
      if (url === "/metrics") return Promise.resolve({ data: mockMetrics });
      if (url === "/version") return Promise.resolve({ data: mockVersion });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Status />);

    await waitFor(() => {
      expect(screen.getByText("System Operations & Freshness")).toBeDefined();
      expect(screen.getByText("HEALTHY")).toBeDefined();
      expect(screen.getByText("CONNECTED")).toBeDefined();
    });
  });

  it("20. renders degraded/disconnected state", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/health") return Promise.resolve({ data: mockHealthDegraded });
      if (url === "/metrics") return Promise.resolve({ data: mockMetrics });
      if (url === "/version") return Promise.resolve({ data: mockVersion });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Status />);

    await waitFor(() => {
      expect(screen.getByText("DEGRADED")).toBeDefined();
      expect(screen.getByText("DISCONNECTED")).toBeDefined();
    });
  });

  it("21. renders dataset metrics and platform version info", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/health") return Promise.resolve({ data: mockHealthHealthy });
      if (url === "/metrics") return Promise.resolve({ data: mockMetrics });
      if (url === "/version") return Promise.resolve({ data: mockVersion });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Status />);

    await waitFor(() => {
      expect(screen.getByText("gold_company")).toBeDefined();
      expect(screen.getByText("gold_salary")).toBeDefined();
      expect(screen.getByText("15.2 min")).toBeDefined();
      expect(screen.getByText("v1.0.0")).toBeDefined();
      expect(screen.getByText("c0808c017e")).toBeDefined();
    });
  });
});

describe("Sprint 8.3 — About Page (/about)", () => {
  it("22. renders architecture sections and pipeline flow", () => {
    renderWithProviders(<About />);

    expect(screen.getByText("About CareerPulse")).toBeDefined();
    expect(screen.getByText("1. What is CareerPulse?")).toBeDefined();
    expect(screen.getByText("2. Architecture Flow Diagram")).toBeDefined();
    expect(screen.getByText("RemoteOK API")).toBeDefined();
    expect(screen.getByText("AWS Glue & S3 Silver")).toBeDefined();
    expect(screen.getByText("Amazon RDS PostgreSQL")).toBeDefined();
    expect(screen.getByText("FastAPI REST Service")).toBeDefined();
    expect(screen.getByText(/6. Data Semantics & Analytical Limitations/i)).toBeDefined();
  });
});

describe("Sprint 8.3 — Shared Features & Interactions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("23. verifies dark mode class structures on cards and headers", () => {
    const { container } = renderWithProviders(<About />);
    const darkElements = container.querySelectorAll(".dark\\:text-white, .dark\\:border-slate-800");
    expect(darkElements.length).toBeGreaterThan(0);
  });

  it("24. renders responsive containers without breaking", () => {
    const { container } = renderWithProviders(<About />);
    expect(container.querySelector(".max-w-5xl")).toBeDefined();
  });

  it("25. triggers refresh re-fetch on status page button click", async () => {
    let healthCalls = 0;
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/health") {
        healthCalls++;
        return Promise.resolve({ data: mockHealthHealthy });
      }
      if (url === "/metrics") return Promise.resolve({ data: mockMetrics });
      if (url === "/version") return Promise.resolve({ data: mockVersion });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Status />);

    const refreshBtn = (await screen.findByRole("button", { name: /refresh/i })) as HTMLButtonElement;
    await waitFor(() => {
      expect(refreshBtn.disabled).toBe(false);
    });

    fireEvent.click(refreshBtn);

    await waitFor(() => {
      expect(healthCalls).toBeGreaterThan(1);
    });
  });
});

describe("Sprint 8.3A — Contract Integrity and Derived Metrics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("26. dynamically calculates salary metrics without hardcoded literals", async () => {
    const dynamicSalary = {
      success: true,
      data: [
        { salary_tier: "Entry (< 50k)", jobs_count: 5, avg_salary_min: 20000, avg_salary_max: 30000 },
        { salary_tier: "Mid (50k-100k)", jobs_count: 10, avg_salary_min: 60000, avg_salary_max: 80000 },
        { salary_tier: "Staff (150k+)", jobs_count: 5, avg_salary_min: 160000, avg_salary_max: 200000 },
        { salary_tier: "Not Specified", jobs_count: 80, avg_salary_min: null, avg_salary_max: null },
      ],
    };

    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: mockSummary });
      if (url.includes("/api/v1/salary")) return Promise.resolve({ data: dynamicSalary });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Salary />);

    await waitFor(() => {
      expect(screen.getAllByText("20").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("80").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("25%").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/20% transparency rate/i)).toBeDefined();
    });
  });

  it("27. derives geography total remote jobs dynamically as sum of data records", async () => {
    const dynamicGeo = {
      success: true,
      data: [
        { country: "Remote", region: "Remote", jobs_count: 15, avg_salary_min: null, avg_salary_max: null, company_count: 10, remote_count: 15, onsite_count: 0, hybrid_count: 0 },
        { country: "United States", region: "onsite", jobs_count: 25, avg_salary_min: 100000, avg_salary_max: 150000, company_count: 12, remote_count: 0, onsite_count: 25, hybrid_count: 0 },
      ],
    };

    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url.includes("/api/v1/geography")) return Promise.resolve({ data: dynamicGeo });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Geography />);

    await waitFor(() => {
      expect(screen.getAllByText("15").length).toBeGreaterThanOrEqual(1);
      expect(screen.queryByText("93")).toBeNull();
    });
  });

  it("28. renders fallback '—' when summary data is absent on Salary page", async () => {
    vi.spyOn(apiClient, "get").mockImplementation((url) => {
      if (url === "/api/v1/summary") return Promise.resolve({ data: { success: true, data: null } });
      if (url.includes("/api/v1/salary")) return Promise.resolve({ data: mockSalary });
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    renderWithProviders(<Salary />);

    await waitFor(() => {
      expect(screen.queryByText("$120,000")).toBeNull();
      expect(screen.queryByText("$750,000")).toBeNull();
    });
  });
});

