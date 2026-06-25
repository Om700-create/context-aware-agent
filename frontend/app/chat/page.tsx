"use client";

import { useState, useRef, useEffect } from "react";
import { sendChat, ChatResponse, Citation } from "@/lib/api";
import { Send, FileText, Loader2, Bot, User } from "lucide-react";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  agent?: string;
  confidence?: number | null;
  citations?: Citation[];
}

const AGENT_LABELS: Record<string, string> = {
  document_agent: "Document Agent",
  appointment_agent: "Appointment Agent",
  memory_agent: "Memory Agent",
};

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hi! I can answer questions about your uploaded documents or help you book an appointment. How can I help?", agent: "supervisor" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [userId, setUserId] = useState<string | undefined>();
  const [bookingState, setBookingState] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setLoading(true);
    try {
      const res: ChatResponse = await sendChat(text, sessionId, userId);
      setSessionId(res.session_id);
      setUserId(res.user_id);
      setBookingState(res.booking_state);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.reply, agent: res.agent, confidence: res.confidence, citations: res.citations },
      ]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: "Something went wrong reaching the backend. Is it running on :8000?", agent: "error" }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <header className="px-8 py-4 border-b border-slate-200 bg-white flex items-center justify-between">
        <div>
          <h1 className="font-semibold">AI Chat</h1>
          <p className="text-xs text-slate-400">Document Q&A + Appointment Booking, with memory and context switching</p>
        </div>
        {bookingState && bookingState !== "IDLE" && (
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
            Booking: {bookingState}
          </span>
        )}
      </header>

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-5 scrollbar-thin">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            {m.role === "assistant" && (
              <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center flex-shrink-0">
                <Bot size={16} className="text-white" />
              </div>
            )}
            <div className={`max-w-xl ${m.role === "user" ? "order-1" : ""}`}>
              {m.role === "assistant" && m.agent && (
                <p className="text-[11px] uppercase tracking-wide text-slate-400 mb-1 font-medium">
                  {AGENT_LABELS[m.agent] || m.agent}
                  {typeof m.confidence === "number" && m.confidence > 0 && (
                    <span className="ml-2 text-emerald-600">{Math.round(m.confidence * 100)}% confidence</span>
                  )}
                </p>
              )}
              <div
                className={`rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                  m.role === "user" ? "bg-brand-600 text-white" : "bg-white border border-slate-200"
                }`}
              >
                {m.content}
              </div>
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 space-y-1.5">
                  {m.citations.map((c, ci) => (
                    <div key={ci} className="flex items-start gap-2 text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
                      <FileText size={13} className="mt-0.5 text-slate-400 flex-shrink-0" />
                      <div>
                        <p className="font-medium text-slate-600">{c.document} · p.{c.page}</p>
                        <p className="text-slate-400">{c.snippet}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {m.role === "user" && (
              <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0 order-2">
                <User size={16} className="text-slate-600" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center">
              <Bot size={16} className="text-white" />
            </div>
            <div className="rounded-2xl px-4 py-2.5 bg-white border border-slate-200">
              <Loader2 size={16} className="animate-spin text-slate-400" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="px-8 py-4 border-t border-slate-200 bg-white">
        <div className="flex items-center gap-2 max-w-3xl">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about a document, or say 'book an appointment'..."
            className="flex-1 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className="bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white rounded-xl px-4 py-2.5"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
