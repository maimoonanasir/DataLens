/**
 * Tests for FilterPanel component.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import FilterPanel from "../src/components/FilterPanel";
import type { FilterOption } from "../src/lib/api";

const mockFilters: FilterOption[] = [
  {
    column: "Country",
    filter_type: "dropdown",
    label: "Country",
    options: { values: ["United Kingdom", "Germany", "France"] },
  },
  {
    column: "InvoiceDate",
    filter_type: "date_range",
    label: "InvoiceDate",
    options: { min: "2009-12-01", max: "2011-12-09" },
  },
];

describe("FilterPanel", () => {
  it("renders filter controls for each filter option", () => {
    const onChange = vi.fn();
    render(
      <FilterPanel filters={mockFilters} activeFilters={{}} onChange={onChange} />
    );
    expect(screen.getByTestId("filter-dropdown-Country")).toBeInTheDocument();
    expect(screen.getByTestId("filter-date-min-InvoiceDate")).toBeInTheDocument();
  });

  it("renders dropdown with all option values", () => {
    const onChange = vi.fn();
    render(
      <FilterPanel filters={mockFilters} activeFilters={{}} onChange={onChange} />
    );
    expect(screen.getByText("United Kingdom")).toBeInTheDocument();
    expect(screen.getByText("Germany")).toBeInTheDocument();
    expect(screen.getByText("France")).toBeInTheDocument();
  });

  it("calls onChange when dropdown value changes", () => {
    const onChange = vi.fn();
    render(
      <FilterPanel filters={mockFilters} activeFilters={{}} onChange={onChange} />
    );
    const dropdown = screen.getByTestId("filter-dropdown-Country");
    fireEvent.change(dropdown, { target: { value: "Germany" } });
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ Country: "Germany" }));
  });

  it("shows Clear All button when filters are active", () => {
    const onChange = vi.fn();
    render(
      <FilterPanel
        filters={mockFilters}
        activeFilters={{ Country: "Germany" }}
        onChange={onChange}
      />
    );
    expect(screen.getByText(/clear all/i)).toBeInTheDocument();
  });

  it("calls onChange with empty object when Clear All is clicked", () => {
    const onChange = vi.fn();
    render(
      <FilterPanel
        filters={mockFilters}
        activeFilters={{ Country: "Germany" }}
        onChange={onChange}
      />
    );
    fireEvent.click(screen.getByText(/clear all/i));
    expect(onChange).toHaveBeenCalledWith({});
  });

  it("returns null when no filters are provided", () => {
    const onChange = vi.fn();
    const { container } = render(
      <FilterPanel filters={[]} activeFilters={{}} onChange={onChange} />
    );
    expect(container.firstChild).toBeNull();
  });
});
