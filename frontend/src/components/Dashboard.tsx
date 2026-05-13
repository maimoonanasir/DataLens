import { type FC } from "react";
import type { ChartData } from "../lib/api";
import ChartCard from "./ChartCard";

interface DashboardProps {
  charts: ChartData[];
  loading: boolean;
}

const Dashboard: FC<DashboardProps> = ({ charts, loading }) => {
  if (loading && charts.length === 0) {
    return (
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <ChartCard key={i} chart={{ spec: {} as never, data: [] }} loading />
          ))}
        </div>
      </div>
    );
  }

  if (charts.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">No visualizations available. Upload a dataset to get started.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Dashboard</h2>
        <span className="text-xs text-gray-400">{charts.length} visualizations</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {charts.map((chart) => (
          <ChartCard key={chart.spec.chart_id} chart={chart} loading={loading} />
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
