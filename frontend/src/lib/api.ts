/**
 * Typed API client for the DataLens backend.
 * All fetch calls go through this module — never call fetch directly in components.
 */

const BASE = "/api";

// ---------------------------------------------------------------------------
// Types (mirroring backend Pydantic models)
// ---------------------------------------------------------------------------

export interface DatasetMeta {
  id: string;
  name: string;
  row_count: number;
  col_count: number;
  file_size: number;
  created_at: string;
}

export interface UploadResponse {
  dataset_id: string;
  name: string;
  row_count: number;
  col_count: number;
  message: string;
}

export interface ColumnProfile {
  name: string;
  dtype: "numeric" | "categorical" | "datetime" | "text";
  null_count: number;
  null_pct: number;
  unique_count: number;
  stats: Record<string, unknown>;
}

export interface ProfileResponse {
  dataset_id: string;
  name: string;
  row_count: number;
  col_count: number;
  columns: ColumnProfile[];
}

export interface ChartSpec {
  chart_id: string;
  chart_type: "bar" | "line" | "area" | "scatter" | "histogram" | "hbar";
  title: string;
  x_col: string | null;
  y_col: string | null;
  agg: string;
  limit: number;
}

export interface ChartDataPoint {
  x?: string | number;
  y?: number;
  name?: string;
  [key: string]: unknown;
}

export interface ChartData {
  spec: ChartSpec;
  data: ChartDataPoint[];
  error?: string;
}

export interface ChartsResponse {
  dataset_id: string;
  specs: ChartSpec[];
  charts: ChartData[];
}

export interface FilterOption {
  column: string;
  filter_type: "dropdown" | "date_range" | "slider" | "text_search";
  label: string;
  options: Record<string, unknown>;
}

export interface FilterOptionsResponse {
  dataset_id: string;
  filters: FilterOption[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  answer: string;
  tool_calls_made: string[];
}

export interface SummaryResponse {
  summary: string;
  generated_at: string;
}

// ---------------------------------------------------------------------------
// Active filters type
// ---------------------------------------------------------------------------

export type FilterState = Record<string, string | { min?: string | number; max?: string | number }>;

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  /** Upload a CSV file and return the new dataset id. */
  uploadCsv: async (file: File): Promise<UploadResponse> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
    return handleResponse<UploadResponse>(res);
  },

  /** List all persisted datasets. */
  listDatasets: async (): Promise<DatasetMeta[]> => {
    const res = await fetch(`${BASE}/datasets`);
    return handleResponse<DatasetMeta[]>(res);
  },

  /** Get column profiles for a dataset. */
  getProfile: async (datasetId: string): Promise<ProfileResponse> => {
    const res = await fetch(`${BASE}/datasets/${datasetId}/profile`);
    return handleResponse<ProfileResponse>(res);
  },

  /** Get chart data with active filters applied. */
  getCharts: async (datasetId: string, filters: FilterState): Promise<ChartsResponse> => {
    const res = await fetch(`${BASE}/datasets/${datasetId}/charts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filters }),
    });
    return handleResponse<ChartsResponse>(res);
  },

  /** Get filter control definitions for a dataset. */
  getFilterOptions: async (datasetId: string): Promise<FilterOptionsResponse> => {
    const res = await fetch(`${BASE}/datasets/${datasetId}/filter-options`);
    return handleResponse<FilterOptionsResponse>(res);
  },

  /** Send a chat message and get an LLM answer. */
  chat: async (
    datasetId: string,
    messages: ChatMessage[],
    filters: FilterState
  ): Promise<ChatResponse> => {
    const res = await fetch(`${BASE}/datasets/${datasetId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages, filters }),
    });
    return handleResponse<ChatResponse>(res);
  },

  /** Generate an executive summary for the dataset. */
  getSummary: async (datasetId: string, filters: FilterState): Promise<SummaryResponse> => {
    const res = await fetch(`${BASE}/datasets/${datasetId}/summary`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filters }),
    });
    return handleResponse<SummaryResponse>(res);
  },
};
