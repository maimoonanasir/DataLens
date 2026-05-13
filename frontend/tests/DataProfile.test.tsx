/**
 * Tests for DataProfile component.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import DataProfile from "../src/components/DataProfile";
import type { ColumnProfile } from "../src/lib/api";

const mockColumns: ColumnProfile[] = [
  {
    name: "InvoiceDate",
    dtype: "datetime",
    null_count: 0,
    null_pct: 0.0,
    unique_count: 365,
    stats: { min: "2009-12-01", max: "2011-12-09" },
  },
  {
    name: "Quantity",
    dtype: "numeric",
    null_count: 5,
    null_pct: 0.5,
    unique_count: 100,
    stats: { min: -80, max: 1000, mean: 12.5, median: 6.0, std: 25.3 },
  },
  {
    name: "Country",
    dtype: "categorical",
    null_count: 0,
    null_pct: 0.0,
    unique_count: 37,
    stats: {
      top_values: [{ value: "United Kingdom", count: 350000 }],
      most_common: "United Kingdom",
    },
  },
];

describe("DataProfile", () => {
  it("renders a card for each column", () => {
    render(
      <DataProfile columns={mockColumns} rowCount={1000000} datasetName="online_retail.csv" />
    );
    expect(screen.getByText("InvoiceDate")).toBeInTheDocument();
    expect(screen.getByText("Quantity")).toBeInTheDocument();
    expect(screen.getByText("Country")).toBeInTheDocument();
  });

  it("shows dataset name and row count", () => {
    render(
      <DataProfile columns={mockColumns} rowCount={1000000} datasetName="online_retail.csv" />
    );
    expect(screen.getByText(/online_retail.csv/)).toBeInTheDocument();
    expect(screen.getByText(/1,000,000 rows/)).toBeInTheDocument();
  });

  it("renders type badges for each column", () => {
    render(
      <DataProfile columns={mockColumns} rowCount={100} datasetName="test.csv" />
    );
    expect(screen.getByText("Date / Time")).toBeInTheDocument();
    expect(screen.getByText("Numeric")).toBeInTheDocument();
    expect(screen.getByText("Categorical")).toBeInTheDocument();
  });

  it("shows null percentage for columns with missing data", () => {
    render(
      <DataProfile columns={mockColumns} rowCount={1000} datasetName="test.csv" />
    );
    expect(screen.getByText("0.5%")).toBeInTheDocument();
  });
});
