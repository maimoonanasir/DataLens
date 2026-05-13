import { type FC } from "react";
import type { ColumnProfile } from "../lib/api";

interface DataProfileProps {
  columns: ColumnProfile[];
  rowCount: number;
  datasetName: string;
}

const DTYPE_LABELS: Record<string, string> = {
  numeric: "Numeric",
  categorical: "Categorical",
  datetime: "Date / Time",
  text: "Text",
};

const DTYPE_BADGE: Record<string, string> = {
  numeric: "badge-numeric",
  categorical: "badge-categorical",
  datetime: "badge-datetime",
  text: "badge-text",
};

const DataProfile: FC<DataProfileProps> = ({ columns, rowCount, datasetName }) => {
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Data Profile</h2>
          <p className="text-sm text-gray-500">
            {datasetName} — {rowCount.toLocaleString()} rows, {columns.length} columns
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {columns.map((col) => (
          <ColumnCard key={col.name} col={col} />
        ))}
      </div>
    </div>
  );
};

const ColumnCard: FC<{ col: ColumnProfile }> = ({ col }) => {
  const statsLines = buildStatsLines(col);

  return (
    <div className="card p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2 mb-2">
        <span
          className="text-sm font-medium text-gray-900 truncate"
          title={col.name}
        >
          {col.name}
        </span>
        <span className={DTYPE_BADGE[col.dtype] ?? "badge bg-gray-100 text-gray-700"}>
          {DTYPE_LABELS[col.dtype] ?? col.dtype}
        </span>
      </div>

      <div className="space-y-1">
        <div className="flex justify-between text-xs text-gray-500">
          <span>Missing</span>
          <span className={col.null_pct > 20 ? "text-red-600 font-medium" : ""}>
            {col.null_pct.toFixed(1)}%
          </span>
        </div>
        <div className="flex justify-between text-xs text-gray-500">
          <span>Unique</span>
          <span>{col.unique_count.toLocaleString()}</span>
        </div>

        {statsLines.map(({ label, value }) => (
          <div key={label} className="flex justify-between text-xs text-gray-500">
            <span>{label}</span>
            <span className="font-mono text-gray-700 truncate max-w-[100px]" title={String(value)}>
              {value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

function buildStatsLines(col: ColumnProfile): { label: string; value: string }[] {
  const lines: { label: string; value: string }[] = [];
  const s = col.stats;

  if (col.dtype === "numeric") {
    if (s.min !== undefined && s.min !== null) lines.push({ label: "Min", value: fmt(s.min) });
    if (s.max !== undefined && s.max !== null) lines.push({ label: "Max", value: fmt(s.max) });
    if (s.mean !== undefined && s.mean !== null) lines.push({ label: "Mean", value: fmt(s.mean) });
  } else if (col.dtype === "datetime") {
    if (s.min) lines.push({ label: "From", value: String(s.min) });
    if (s.max) lines.push({ label: "To", value: String(s.max) });
  } else if (col.dtype === "categorical") {
    const top = (s.top_values as Array<{ value: string; count: number }>)?.[0];
    if (top) lines.push({ label: "Top value", value: `${top.value} (${top.count.toLocaleString()})` });
  } else if (col.dtype === "text") {
    if (s.avg_length !== null && s.avg_length !== undefined)
      lines.push({ label: "Avg length", value: `${Math.round(Number(s.avg_length))} chars` });
  }

  return lines;
}

function fmt(v: unknown): string {
  const n = Number(v);
  if (isNaN(n)) return String(v);
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n % 1 === 0 ? n.toString() : n.toFixed(2);
}

export default DataProfile;
