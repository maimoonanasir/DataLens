import { type FC, useState, useEffect, useCallback } from "react";
import { BarChart2, Database, RefreshCw } from "lucide-react";
import {
  api,
  type UploadResponse,
  type ProfileResponse,
  type ChartsResponse,
  type FilterOptionsResponse,
  type FilterState,
} from "./lib/api";
import UploadZone from "./components/UploadZone";
import DataProfile from "./components/DataProfile";
import Dashboard from "./components/Dashboard";
import FilterPanel from "./components/FilterPanel";
import ChatPanel from "./components/ChatPanel";
import ExecutiveSummary from "./components/ExecutiveSummary";

// ---------------------------------------------------------------------------
// App state
// ---------------------------------------------------------------------------

interface DatasetState {
  id: string;
  name: string;
  rowCount: number;
  colCount: number;
}

const App: FC = () => {
  const [dataset, setDataset] = useState<DatasetState | null>(null);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [chartsData, setChartsData] = useState<ChartsResponse | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptionsResponse | null>(null);
  const [activeFilters, setActiveFilters] = useState<FilterState>({});
  const [loading, setLoading] = useState(false);
  const [chartsLoading, setChartsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"dashboard" | "profile" | "chat" | "summary">(
    "dashboard"
  );

  // On mount: restore the last uploaded dataset from the API
  useEffect(() => {
    const restore = async () => {
      try {
        const datasets = await api.listDatasets();
        if (datasets.length > 0) {
          const latest = datasets[0];
          setDataset({
            id: latest.id,
            name: latest.name,
            rowCount: latest.row_count,
            colCount: latest.col_count,
          });
        }
      } catch {
        // Backend may not be running yet
      }
    };
    restore();
  }, []);

  // Fetch profile and filter options when dataset changes
  useEffect(() => {
    if (!dataset) return;
    const fetch = async () => {
      setLoading(true);
      setError(null);
      try {
        const [prof, fo] = await Promise.all([
          api.getProfile(dataset.id),
          api.getFilterOptions(dataset.id),
        ]);
        setProfile(prof);
        setFilterOptions(fo);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dataset profile.");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [dataset]);

  // Fetch charts whenever dataset or filters change
  const fetchCharts = useCallback(
    async (filters: FilterState) => {
      if (!dataset) return;
      setChartsLoading(true);
      try {
        const response = await api.getCharts(dataset.id, filters);
        setChartsData(response);
      } catch (err) {
        console.error("Chart fetch error:", err);
      } finally {
        setChartsLoading(false);
      }
    },
    [dataset]
  );

  useEffect(() => {
    fetchCharts(activeFilters);
  }, [fetchCharts, activeFilters]);

  const handleUploadSuccess = (response: UploadResponse) => {
    setDataset({
      id: response.dataset_id,
      name: response.name,
      rowCount: response.row_count,
      colCount: response.col_count,
    });
    setActiveFilters({});
    setChartsData(null);
    setProfile(null);
    setFilterOptions(null);
    setActiveTab("dashboard");
  };

  const handleFilterChange = (filters: FilterState) => {
    setActiveFilters(filters);
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-indigo-600 p-1.5">
              <BarChart2 className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900">DataLens</span>
            {dataset && (
              <span className="hidden sm:inline text-xs text-gray-500 ml-2">
                <Database className="inline h-3 w-3 mr-1" />
                {dataset.name} · {dataset.rowCount.toLocaleString()} rows
              </span>
            )}
          </div>
          {dataset && (
            <button
              onClick={() => fetchCharts(activeFilters)}
              className="btn-secondary text-xs"
              title="Refresh charts"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </button>
          )}
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Upload zone — always visible */}
        <section>
          <UploadZone onUploadSuccess={handleUploadSuccess} />
        </section>

        {/* Error state */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Dashboard content — shown once a dataset is loaded */}
        {dataset && (
          <>
            {/* Filter panel */}
            {filterOptions && filterOptions.filters.length > 0 && (
              <section>
                <FilterPanel
                  filters={filterOptions.filters}
                  activeFilters={activeFilters}
                  onChange={handleFilterChange}
                />
              </section>
            )}

            {/* Tab navigation */}
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex gap-6">
                {(
                  [
                    { id: "dashboard", label: "Dashboard" },
                    { id: "profile", label: "Data Profile" },
                    { id: "chat", label: "Chat" },
                    { id: "summary", label: "Executive Summary" },
                  ] as const
                ).map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? "border-indigo-600 text-indigo-600"
                        : "border-transparent text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab content */}
            <section>
              {activeTab === "dashboard" && (
                <Dashboard charts={chartsData?.charts ?? []} loading={chartsLoading} />
              )}

              {activeTab === "profile" && profile && (
                <DataProfile
                  columns={profile.columns}
                  rowCount={profile.row_count}
                  datasetName={profile.name}
                />
              )}

              {activeTab === "chat" && (
                <ChatPanel datasetId={dataset.id} filters={activeFilters} />
              )}

              {activeTab === "summary" && (
                <ExecutiveSummary datasetId={dataset.id} filters={activeFilters} />
              )}
            </section>
          </>
        )}

        {/* Empty state — no dataset loaded */}
        {!dataset && !error && (
          <div className="text-center py-16 text-gray-400">
            <BarChart2 className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">Upload a CSV file above to get started</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
