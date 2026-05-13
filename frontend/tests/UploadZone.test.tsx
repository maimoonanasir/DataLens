/**
 * Tests for UploadZone component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import UploadZone from "../src/components/UploadZone";

// Mock the api module
vi.mock("../src/lib/api", () => ({
  api: {
    uploadCsv: vi.fn(),
  },
}));

import { api } from "../src/lib/api";

describe("UploadZone", () => {
  const mockOnSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the upload zone with correct text", () => {
    render(<UploadZone onUploadSuccess={mockOnSuccess} />);
    expect(screen.getByText(/upload your csv file/i)).toBeInTheDocument();
    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
  });

  it("shows error when a non-CSV file is selected", async () => {
    render(<UploadZone onUploadSuccess={mockOnSuccess} />);

    const input = screen.getByTestId("file-input");
    const file = new File(["data"], "data.xlsx", { type: "application/vnd.ms-excel" });

    await fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText(/only .csv files/i)).toBeInTheDocument();
    expect(mockOnSuccess).not.toHaveBeenCalled();
  });

  it("calls onUploadSuccess when upload succeeds", async () => {
    const mockResponse = {
      dataset_id: "abc123",
      name: "test.csv",
      row_count: 100,
      col_count: 8,
      message: "Success",
    };
    (api.uploadCsv as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

    render(<UploadZone onUploadSuccess={mockOnSuccess} />);
    const input = screen.getByTestId("file-input");
    const file = new File(["col1,col2\n1,2\n"], "test.csv", { type: "text/csv" });

    await fireEvent.change(input, { target: { files: [file] } });

    // Wait for async processing
    await vi.waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalledWith(mockResponse);
    });
  });

  it("shows error message when upload API fails", async () => {
    (api.uploadCsv as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("File too large")
    );

    render(<UploadZone onUploadSuccess={mockOnSuccess} />);
    const input = screen.getByTestId("file-input");
    const file = new File(["col1,col2\n1,2"], "test.csv", { type: "text/csv" });

    await fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText(/file too large/i)).toBeInTheDocument();
  });

  it("shows error for file exceeding 50MB client-side check", async () => {
    render(<UploadZone onUploadSuccess={mockOnSuccess} />);
    const input = screen.getByTestId("file-input");

    // Create a mock file that reports large size
    const file = new File(["x"], "huge.csv", { type: "text/csv" });
    Object.defineProperty(file, "size", { value: 51 * 1024 * 1024 });

    await fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText(/exceeds the 50 mb limit/i)).toBeInTheDocument();
  });
});
