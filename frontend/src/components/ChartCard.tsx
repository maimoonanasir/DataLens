import { type FC } from "react";
import {
  ResponsiveContainer,
  BarChart, Bar,
  LineChart, Line,
  AreaChart, Area,
  ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from "recharts";
import type { ChartData } from "../lib/api";

interface ChartCardProps {
  chart: ChartData;
  loading?: boolean;
}

const COLORS = [
  "#6366f1", "#8b5cf6", "#06b6d4", "#10b981",
  "#f59e0b", "#ef4444", "#ec4899", "#14b8a6",
];

const ChartCard: FC<ChartCardProps> = ({ chart, loading = false }) => {
  if (loading) {
    return (
      <div className="card animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4" />
        <div className="h-48 bg-gray-100 rounded" />
      </div>
    );
  }

  if (chart.error) {
    return (
      <div className="card border-red-200">
        <p className="text-sm font-medium text-gray-700 mb-2">{chart.spec.title}</p>
        <p className="text-xs text-red-500">Chart error: {chart.error}</p>
      </div>
    );
  }

  if (!chart.data || chart.data.length === 0) {
    return (
      <div className="card">
        <p className="text-sm font-medium text-gray-700 mb-2">{chart.spec.title}</p>
        <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
          No data for current filters
        </div>
      </div>
    );
  }

  const renderChart = () => {
    const { chart_type } = chart.spec;

    if (chart_type === "bar" || chart_type === "histogram") {
      return (
        <BarChart data={chart.data} margin={{ top: 4, right: 8, bottom: 40, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 10, fill: "#6b7280" }}
            interval={0}
            angle={chart.data.length > 8 ? -35 : 0}
            textAnchor={chart.data.length > 8 ? "end" : "middle"}
            height={chart.data.length > 8 ? 60 : 30}
          />
          <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} width={45} />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
            formatter={(v: number) => [v.toLocaleString(), chart.spec.y_col ?? "count"]}
          />
          <Bar dataKey="y" radius={[4, 4, 0, 0]}>
            {chart.data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      );
    }

    if (chart_type === "hbar") {
      return (
        <BarChart
          data={chart.data}
          layout="vertical"
          margin={{ top: 4, right: 8, bottom: 8, left: 80 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 10, fill: "#6b7280" }} />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 10, fill: "#6b7280" }}
            width={78}
          />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
            formatter={(v: number) => [v.toLocaleString(), chart.spec.y_col ?? "count"]}
          />
          <Bar dataKey="y" radius={[0, 4, 4, 0]}>
            {chart.data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      );
    }

    if (chart_type === "line") {
      return (
        <LineChart data={chart.data} margin={{ top: 4, right: 8, bottom: 30, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 10, fill: "#6b7280" }}
            angle={-35}
            textAnchor="end"
            height={50}
          />
          <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} width={50} />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
            formatter={(v: number) => [v.toLocaleString(), chart.spec.y_col ?? "value"]}
          />
          <Line
            type="monotone"
            dataKey="y"
            stroke="#6366f1"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      );
    }

    if (chart_type === "area") {
      return (
        <AreaChart data={chart.data} margin={{ top: 4, right: 8, bottom: 30, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#6b7280" }} angle={-35} textAnchor="end" height={50} />
          <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} width={50} />
          <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
          <Area type="monotone" dataKey="y" stroke="#6366f1" fill="#e0e7ff" strokeWidth={2} />
        </AreaChart>
      );
    }

    if (chart_type === "scatter") {
      return (
        <ScatterChart margin={{ top: 4, right: 8, bottom: 30, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="x"
            name={chart.spec.x_col ?? "x"}
            tick={{ fontSize: 10, fill: "#6b7280" }}
            label={{ value: chart.spec.x_col, position: "insideBottom", offset: -20, fontSize: 11 }}
          />
          <YAxis
            dataKey="y"
            name={chart.spec.y_col ?? "y"}
            tick={{ fontSize: 10, fill: "#6b7280" }}
            width={50}
          />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
            formatter={(v: number, name: string) => [v.toLocaleString(), name]}
          />
          <Scatter data={chart.data} fill="#6366f1" opacity={0.6} />
        </ScatterChart>
      );
    }

    return null;
  };

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 truncate" title={chart.spec.title}>
        {chart.spec.title}
      </h3>
      <ResponsiveContainer width="100%" height={240}>
        {renderChart() ?? <div />}
      </ResponsiveContainer>
    </div>
  );
};

export default ChartCard;
