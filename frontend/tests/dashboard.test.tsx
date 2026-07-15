import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import DashboardPage from "@/app/dashboard/page";
import { Sidebar } from "@/components/layout/sidebar";
import { SystemReadiness } from "@/components/dashboard/system-readiness";
vi.mock("next/navigation", () => ({ usePathname: () => "/dashboard" }));
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  ComposedChart: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  Area: () => null,
  CartesianGrid: () => null,
  Line: () => null,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}));
describe("dashboard", () => {
  it("renders the dashboard title", () => {
    render(<DashboardPage />);
    expect(
      screen.getByRole("heading", { name: "Dashboard" }),
    ).toBeInTheDocument();
  });
  it("renders the system readiness panel", () => {
    render(<DashboardPage />);
    expect(screen.getByText("System readiness")).toBeInTheDocument();
  });
  it("renders sidebar navigation items", () => {
    render(<Sidebar />);
    expect(screen.getAllByText("Revenue Forecasts").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Model Trust Center").length).toBeGreaterThan(0);
  });
  it("provides an accessible mobile sidebar control", () => {
    render(<Sidebar />);
    expect(screen.getByLabelText("Open navigation menu")).toBeInTheDocument();
  });
});
describe("API connectivity", () => {
  it("shows a loading state", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => undefined)),
    );
    render(<SystemReadiness />);
    expect(screen.getByText(/Checking API connectivity/)).toBeInTheDocument();
  });
  it("shows connected backend status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          application: {
            name: "CausalCast AI",
            version: "0.1.0",
            environment: "test",
          },
          backend: { framework: "FastAPI", status: "operational" },
          database: { type: "SQLite", status: "connected" },
          modules: {},
        }),
      }),
    );
    render(<SystemReadiness />);
    await waitFor(() =>
      expect(
        screen.getByText("Operational", { selector: "span" }),
      ).toBeInTheDocument(),
    );
  });
  it("handles failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<SystemReadiness />);
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Backend unavailable",
      ),
    );
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });
});
