import { type FC, useCallback, useRef, useState } from "react";
import { Upload, FileText, AlertCircle, CheckCircle2 } from "lucide-react";
import { api, type UploadResponse } from "../lib/api";

interface UploadZoneProps {
  onUploadSuccess: (response: UploadResponse) => void;
}

type UploadState = "idle" | "uploading" | "success" | "error";

const UploadZone: FC<UploadZoneProps> = ({ onUploadSuccess }) => {
  const [state, setState] = useState<UploadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".csv")) {
        setError("Only .csv files are supported. Please upload a CSV file.");
        setState("error");
        return;
      }

      if (file.size > 200 * 1024 * 1024) {
        setError(`File size ${(file.size / 1024 / 1024).toFixed(1)} MB exceeds the 50 MB limit.`);
        setState("error");
        return;
      }

      setFileName(file.name);
      setState("uploading");
      setError(null);

      try {
        const response = await api.uploadCsv(file);
        setState("success");
        onUploadSuccess(response);
      } catch (err) {
        setState("error");
        setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
      }
    },
    [onUploadSuccess]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleClick = () => inputRef.current?.click();

  const reset = () => {
    setState("idle");
    setError(null);
    setFileName(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload CSV file"
        onClick={state === "idle" || state === "error" ? handleClick : undefined}
        onKeyDown={(e) => e.key === "Enter" && handleClick()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`
          relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed
          p-12 text-center transition-all duration-200 cursor-pointer
          ${isDragging ? "border-indigo-500 bg-indigo-50" : "border-gray-300 hover:border-indigo-400 hover:bg-gray-50"}
          ${state === "success" ? "border-green-400 bg-green-50 cursor-default" : ""}
          ${state === "error" ? "border-red-400 bg-red-50" : ""}
          ${state === "uploading" ? "cursor-wait" : ""}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleChange}
          data-testid="file-input"
        />

        {state === "idle" && (
          <>
            <div className="rounded-full bg-indigo-100 p-4 mb-4">
              <Upload className="h-8 w-8 text-indigo-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Upload your CSV file</h3>
            <p className="text-sm text-gray-500 mb-3">Drag and drop, or click to browse</p>
            <p className="text-xs text-gray-400">Supports any CSV up to 200 MB</p>
          </>
        )}

        {state === "uploading" && (
          <>
            <div className="rounded-full bg-indigo-100 p-4 mb-4 animate-pulse">
              <FileText className="h-8 w-8 text-indigo-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-700 mb-1">Uploading {fileName}…</h3>
            <p className="text-sm text-gray-500">Parsing and storing your data</p>
            <div className="mt-4 w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-indigo-500 rounded-full animate-[loading_1.5s_ease-in-out_infinite]" />
            </div>
          </>
        )}

        {state === "success" && (
          <>
            <div className="rounded-full bg-green-100 p-4 mb-4">
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-green-800 mb-1">
              {fileName} uploaded successfully
            </h3>
            <p className="text-sm text-green-600 mb-4">Your dashboard is ready below</p>
            <button onClick={reset} className="btn-secondary text-xs">
              Upload a different file
            </button>
          </>
        )}

        {state === "error" && (
          <>
            <div className="rounded-full bg-red-100 p-4 mb-4">
              <AlertCircle className="h-8 w-8 text-red-600" />
            </div>
            <h3 className="text-lg font-semibold text-red-800 mb-1">Upload failed</h3>
            <p className="text-sm text-red-600 mb-4">{error}</p>
            <button onClick={reset} className="btn-secondary">
              Try again
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default UploadZone;
