import { type FC, useState } from "react";
import { Sparkles, Copy, CheckCheck, Loader2, FileText } from "lucide-react";
import { api, type FilterState } from "../lib/api";

interface ExecutiveSummaryProps {
  datasetId: string;
  filters: FilterState;
}

const ExecutiveSummary: FC<ExecutiveSummaryProps> = ({ datasetId, filters }) => {
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [generatedAt, setGeneratedAt] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getSummary(datasetId, filters);
      setSummary(response.summary);
      setGeneratedAt(response.generated_at);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate summary.");
    } finally {
      setLoading(false);
    }
  };

  const copy = async () => {
    if (!summary) return;
    await navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
          <FileText className="h-4 w-4 text-indigo-600" />
          Executive Summary
        </h3>
        {summary && (
          <button onClick={copy} className="btn-secondary text-xs gap-1.5">
            {copied ? (
              <>
                <CheckCheck className="h-3.5 w-3.5 text-green-600" /> Copied
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" /> Copy
              </>
            )}
          </button>
        )}
      </div>

      {!summary && !loading && !error && (
        <div className="text-center py-8">
          <div className="rounded-full bg-indigo-50 p-4 inline-flex mb-3">
            <Sparkles className="h-6 w-6 text-indigo-500" />
          </div>
          <p className="text-sm text-gray-600 mb-4 max-w-sm mx-auto">
            Generate an AI-powered executive summary highlighting key patterns, trends, and
            actionable insights in your data.
          </p>
          <button onClick={generate} className="btn-primary">
            <Sparkles className="h-4 w-4" />
            Generate Executive Summary
          </button>
        </div>
      )}

      {loading && (
        <div className="text-center py-8">
          <Loader2 className="h-8 w-8 text-indigo-500 animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-500">Analysing your data and crafting insights…</p>
          <p className="text-xs text-gray-400 mt-1">This may take up to 30 seconds</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          <p className="font-medium mb-1">Summary generation failed</p>
          <p>{error}</p>
          <button onClick={generate} className="btn-secondary text-xs mt-3">
            Try again
          </button>
        </div>
      )}

      {summary && !loading && (
        <>
          <div className="prose prose-sm max-w-none">
            {summary.split("\n\n").map((para, i) => (
              <p key={i} className="text-sm text-gray-700 leading-relaxed mb-3 last:mb-0">
                {para}
              </p>
            ))}
          </div>
          {generatedAt && (
            <p className="text-xs text-gray-400 mt-4 pt-3 border-t border-gray-100">
              Generated at {new Date(generatedAt).toLocaleString()} · Powered by Claude
            </p>
          )}
          <button onClick={generate} className="btn-secondary text-xs mt-3 gap-1.5">
            <Sparkles className="h-3.5 w-3.5" /> Regenerate
          </button>
        </>
      )}
    </div>
  );
};

export default ExecutiveSummary;
