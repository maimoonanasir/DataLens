/**
 * Tests for ChatPanel component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ChatPanel from "../src/components/ChatPanel";

vi.mock("../src/lib/api", () => ({
  api: {
    chat: vi.fn(),
  },
}));

import { api } from "../src/lib/api";

describe("ChatPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the chat input and send button", () => {
    render(<ChatPanel datasetId="abc123" filters={{}} />);
    expect(screen.getByTestId("chat-input")).toBeInTheDocument();
    expect(screen.getByTestId("chat-send")).toBeInTheDocument();
  });

  it("renders the welcome message", () => {
    render(<ChatPanel datasetId="abc123" filters={{}} />);
    expect(screen.getByText(/hello/i)).toBeInTheDocument();
  });

  it("send button is disabled when input is empty", () => {
    render(<ChatPanel datasetId="abc123" filters={{}} />);
    const sendButton = screen.getByTestId("chat-send");
    expect(sendButton).toBeDisabled();
  });

  it("send button is enabled when input has text", () => {
    render(<ChatPanel datasetId="abc123" filters={{}} />);
    const input = screen.getByTestId("chat-input");
    fireEvent.change(input, { target: { value: "Which country has the most sales?" } });
    const sendButton = screen.getByTestId("chat-send");
    expect(sendButton).not.toBeDisabled();
  });

  it("shows user message after sending", async () => {
    (api.chat as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      answer: "United Kingdom has the highest revenue.",
      tool_calls_made: ["query_data"],
    });

    render(<ChatPanel datasetId="abc123" filters={{}} />);
    const input = screen.getByTestId("chat-input");
    fireEvent.change(input, { target: { value: "Which country?" } });
    fireEvent.click(screen.getByTestId("chat-send"));

    expect(await screen.findByText("Which country?")).toBeInTheDocument();
    expect(await screen.findByText(/United Kingdom has the highest revenue/i)).toBeInTheDocument();
  });

  it("shows sample questions when no messages sent yet", () => {
    render(<ChatPanel datasetId="abc123" filters={{}} />);
    expect(screen.getByText(/try asking/i)).toBeInTheDocument();
  });
});
