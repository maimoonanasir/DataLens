import { type FC, useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, AlertCircle } from "lucide-react";
import { api, type ChatMessage, type FilterState } from "../lib/api";

interface ChatPanelProps {
  datasetId: string;
  filters: FilterState;
}

interface LocalMessage extends ChatMessage {
  id: string;
  loading?: boolean;
  error?: boolean;
}

const SAMPLE_QUESTIONS = [
  "What is the most common primary diagnosis?",
  "How many patients were readmitted within 30 days?",
  "What is the average time spent in hospital?",
  "Which age group has the most admissions?",
  "What percentage of patients have diabetes medication?",
];

const ChatPanel: FC<ChatPanelProps> = ({ datasetId, filters }) => {
  const [messages, setMessages] = useState<LocalMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hello! I'm DataLens AI. Ask me anything about your dataset — I'll query it directly to give you accurate, data-grounded answers.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: LocalMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text.trim(),
    };

    const loadingMsg: LocalMessage = {
      id: `loading-${Date.now()}`,
      role: "assistant",
      content: "",
      loading: true,
    };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);
    setInput("");
    setIsLoading(true);

    // Build history (exclude welcome message and loading messages)
    const history: ChatMessage[] = messages
      .filter((m) => m.id !== "welcome" && !m.loading && !m.error)
      .map(({ role, content }) => ({ role, content }));
    history.push({ role: "user", content: text.trim() });

    try {
      const response = await api.chat(datasetId, history, filters);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? { ...m, content: response.answer, loading: false }
            : m
        )
      );
    } catch (err) {
      const errorText =
        err instanceof Error ? err.message : "Sorry, I couldn't process that. Please try again.";
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? { ...m, content: errorText, loading: false, error: true }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <div className="card flex flex-col h-[500px]">
      <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
        <Bot className="h-4 w-4 text-indigo-600" />
        Chat with your data
      </h3>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 mb-3">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Sample questions */}
      {messages.length <= 1 && (
        <div className="mb-3">
          <p className="text-xs text-gray-400 mb-2">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => sendMessage(q)}
                className="text-xs px-3 py-1.5 rounded-full border border-indigo-200 text-indigo-700 hover:bg-indigo-50 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="flex gap-2 items-end">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your data…"
          disabled={isLoading}
          rows={2}
          className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:bg-gray-50"
          data-testid="chat-input"
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || isLoading}
          className="btn-primary shrink-0"
          data-testid="chat-send"
          aria-label="Send message"
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
};

const MessageBubble: FC<{ msg: LocalMessage }> = ({ msg }) => {
  const isUser = msg.role === "user";

  return (
    <div className={`flex gap-2 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div
        className={`shrink-0 rounded-full p-1.5 ${isUser ? "bg-indigo-100" : "bg-gray-100"}`}
      >
        {isUser ? (
          <User className="h-3.5 w-3.5 text-indigo-600" />
        ) : (
          <Bot className="h-3.5 w-3.5 text-gray-600" />
        )}
      </div>
      <div
        className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
          isUser
            ? "bg-indigo-600 text-white rounded-tr-sm"
            : msg.error
            ? "bg-red-50 text-red-700 border border-red-200"
            : "bg-gray-100 text-gray-800 rounded-tl-sm"
        }`}
      >
        {msg.loading ? (
          <div className="flex gap-1 items-center py-1">
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
          </div>
        ) : msg.error ? (
          <div className="flex items-start gap-1.5">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{msg.content}</span>
          </div>
        ) : (
          <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
        )}
      </div>
    </div>
  );
};

export default ChatPanel;
