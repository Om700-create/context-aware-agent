export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api";

export interface Citation {
  document: string;
  page: number;
  snippet: string;
}

export interface ChatResponse {
  session_id: string;
  user_id: string;
  reply: string;
  agent: string;
  confidence: number | null;
  citations: Citation[];
  booking_state: string | null;
  meta: Record<string, unknown>;
}

export async function sendChat(message: string, sessionId?: string, userId?: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId, user_id: userId }),
  });
  if (!res.ok) throw new Error(`Chat request failed: ${res.status}`);
  return res.json();
}

export interface DocumentItem {
  id: string;
  filename: string;
  num_pages: number;
  num_chunks: number;
  size_bytes: number;
  status: string;
  uploaded_at: string;
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/documents/upload`, { method: "POST", body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function listDocuments(): Promise<DocumentItem[]> {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error("Failed to load documents");
  return res.json();
}

export interface AppointmentItem {
  id: string;
  user_id: string;
  full_name: string;
  email: string;
  phone: string;
  appointment_date: string;
  original_date_text: string | null;
  status: string;
  created_at: string;
}

export async function listAppointments(): Promise<AppointmentItem[]> {
  const res = await fetch(`${API_BASE}/appointments`);
  if (!res.ok) throw new Error("Failed to load appointments");
  return res.json();
}

export interface AnalyticsSummary {
  total_chats: number;
  total_appointments: number;
  total_users: number;
  total_documents: number;
  agent_usage: Record<string, number>;
  avg_response_time_ms: number;
}

export async function getAnalytics(): Promise<AnalyticsSummary> {
  const res = await fetch(`${API_BASE}/analytics`);
  if (!res.ok) throw new Error("Failed to load analytics");
  return res.json();
}
