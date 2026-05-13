import { type FC } from "react";
import { SlidersHorizontal, X } from "lucide-react";
import type { FilterOption, FilterState } from "../lib/api";

interface FilterPanelProps {
  filters: FilterOption[];
  activeFilters: FilterState;
  onChange: (filters: FilterState) => void;
}

const FilterPanel: FC<FilterPanelProps> = ({ filters, activeFilters, onChange }) => {
  const activeCount = Object.keys(activeFilters).filter(
    (k) => activeFilters[k] !== "" && activeFilters[k] !== undefined
  ).length;

  const clearAll = () => onChange({});

  const setFilter = (column: string, value: FilterState[string]) => {
    if (value === "" || value === undefined) {
      const next = { ...activeFilters };
      delete next[column];
      onChange(next);
    } else {
      onChange({ ...activeFilters, [column]: value });
    }
  };

  if (filters.length === 0) return null;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-900">Global Filters</h3>
          {activeCount > 0 && (
            <span className="badge bg-indigo-100 text-indigo-700">{activeCount} active</span>
          )}
        </div>
        {activeCount > 0 && (
          <button onClick={clearAll} className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1">
            <X className="h-3 w-3" /> Clear all
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-4">
        {filters.map((filter) => (
          <FilterControl
            key={filter.column}
            filter={filter}
            value={activeFilters[filter.column]}
            onChange={(v) => setFilter(filter.column, v)}
          />
        ))}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Individual filter control
// ---------------------------------------------------------------------------

interface FilterControlProps {
  filter: FilterOption;
  value: FilterState[string];
  onChange: (value: FilterState[string]) => void;
}

const FilterControl: FC<FilterControlProps> = ({ filter, value, onChange }) => {
  if (filter.filter_type === "dropdown") {
    const values = (filter.options.values as string[]) ?? [];
    const selected = typeof value === "string" ? value : "";

    return (
      <div className="flex flex-col gap-1 min-w-[160px]">
        <label className="text-xs font-medium text-gray-600">{filter.label}</label>
        <select
          value={selected}
          onChange={(e) => onChange(e.target.value)}
          className="text-sm rounded-lg border border-gray-300 px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          data-testid={`filter-dropdown-${filter.column}`}
        >
          <option value="">All</option>
          {values.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </div>
    );
  }

  if (filter.filter_type === "date_range") {
    const range = (typeof value === "object" ? value : {}) as { min?: string; max?: string };
    const minDate = filter.options.min as string;
    const maxDate = filter.options.max as string;

    return (
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-gray-600">{filter.label}</label>
        <div className="flex items-center gap-2">
          <input
            type="date"
            min={minDate}
            max={maxDate}
            value={range.min ?? ""}
            onChange={(e) => onChange({ ...range, min: e.target.value || undefined })}
            className="text-sm rounded-lg border border-gray-300 px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid={`filter-date-min-${filter.column}`}
          />
          <span className="text-xs text-gray-400">to</span>
          <input
            type="date"
            min={minDate}
            max={maxDate}
            value={range.max ?? ""}
            onChange={(e) => onChange({ ...range, max: e.target.value || undefined })}
            className="text-sm rounded-lg border border-gray-300 px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid={`filter-date-max-${filter.column}`}
          />
        </div>
      </div>
    );
  }

  if (filter.filter_type === "slider") {
    const range = (typeof value === "object" ? value : {}) as { min?: number; max?: number };
    const sliderMin = filter.options.min as number;
    const sliderMax = filter.options.max as number;

    return (
      <div className="flex flex-col gap-1 min-w-[200px]">
        <label className="text-xs font-medium text-gray-600">
          {filter.label}
          {range.min !== undefined && range.max !== undefined && (
            <span className="text-gray-400 font-normal ml-1">
              ({range.min} – {range.max})
            </span>
          )}
        </label>
        <div className="flex items-center gap-2">
          <input
            type="number"
            placeholder={String(sliderMin)}
            value={range.min ?? ""}
            min={sliderMin}
            max={sliderMax}
            onChange={(e) =>
              onChange({ ...range, min: e.target.value ? Number(e.target.value) : undefined })
            }
            className="text-sm rounded-lg border border-gray-300 px-2 py-1.5 w-24 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid={`filter-slider-min-${filter.column}`}
          />
          <span className="text-xs text-gray-400">to</span>
          <input
            type="number"
            placeholder={String(sliderMax)}
            value={range.max ?? ""}
            min={sliderMin}
            max={sliderMax}
            onChange={(e) =>
              onChange({ ...range, max: e.target.value ? Number(e.target.value) : undefined })
            }
            className="text-sm rounded-lg border border-gray-300 px-2 py-1.5 w-24 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid={`filter-slider-max-${filter.column}`}
          />
        </div>
      </div>
    );
  }

  return null;
};

export default FilterPanel;
