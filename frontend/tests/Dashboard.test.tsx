/**
 * Tests for Dashboard component.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Dashboard from "../src/components/Dashboard";
import type { ChartData, ChartSpec } from "../src/lib/api";

// Recharts uses ResizeObserver — mock it for jsdom
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

function makeChart(id: string, type: ChartSpec["chart_type"]): ChartData {
  return {
    spec: {
      chart_id: id,
      chart_type: type,
      title: `Chart ${id}`,
      x_col: "Country",
      y_col: "Revenue",
      agg: "sum",
      limit: 20,
    },
    data: [
      { x: "UK", y: 1000, name: "UK" },
      { x: "DE", y: 500, name: "DE" },
    ],
  };
}

describe("Dashboard", () => {
  it("renders the correct number of chart cards", () => {
    const charts = [
      makeChart("bar_country", "bar"),
      makeChart("line_date", "line"),
      makeChart("hist_qty", "histogram"),
      makeChart("scatter", "scatter"),
    ];
    render(<Dashboard charts={charts} loading={false} />);
    expect(screen.getAllByText(/Chart/i).length).toBeGreaterThanOrEqual(4);
  });

  it("shows empty state when no charts provided", () => {
    render(<Dashboard charts={[]} loading={false} />);
    expect(screen.getByText(/no visualizations available/i)).toBeInTheDocument();
  });

  it("shows loading skeletons when loading=true and no charts", () => {
    const { container } = render(<Dashboard charts={[]} loading={true} />);
    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders chart titles from spec", () => {
    const charts = [makeChart("bar_country", "bar")];
    render(<Dashboard charts={charts} loading={false} />);
    expect(screen.getByText("Chart bar_country")).toBeInTheDocument();
  });

  it("shows visualization count in header", () => {
    const charts = [
      makeChart("c1", "bar"),
      makeChart("c2", "line"),
      makeChart("c3", "histogram"),
      makeChart("c4", "scatter"),
    ];
    render(<Dashboard charts={charts} loading={false} />);
    expect(screen.getByText(/4 visualizations/i)).toBeInTheDocument();
  });
});
