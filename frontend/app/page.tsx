"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getAnalytics, AnalyticsSummary } from "@/lib/api";
import { MessageSquare, FileText, Calendar, Users } from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    getAnalytics().then(setStats).catch(() => setStats(null));
  }, []);

  const cards = [
    { label: "Total Chats", value: stats?.total_chats ?? "—", icon: MessageSquare, color: "bg-indigo-50 text-indigo-600" },
    { label: "Total Appointments", value: stats?.total_appointments ?? "—", icon: Calendar, color: "bg-emerald-50 text-emerald-600" },
    { label: "Total Users", value: stats?.total_users ?? "—", icon: Users, color: "bg-amber-50 text-amber-600" },
    { label: "Total Documents", value: stats?.total_documents ?? "—", icon: FileText, color: "bg-rose-50 text-rose-600" },
  ];

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Dashboard</h1>
      <p className="text-slate-500 mb-8">Overview of your multi-agent conversational AI platform.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        {cards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border border-slate-200 p-5">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${color}`}>
              <Icon size={18} />
            </div>
            <p className="text-2xl font-semibold">{value}</p>
            <p className="text-sm text-slate-500">{label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link href="/chat" className="block bg-brand-600 hover:bg-brand-700 transition-colors text-white rounded-xl p-6">
          <h3 className="font-semibold text-lg mb-1">Start a conversation →</h3>
          <p className="text-brand-100 text-sm">Ask questions about your documents or book an appointment.</p>
        </Link>
        <Link href="/documents" className="block bg-white border border-slate-200 hover:border-brand-300 transition-colors rounded-xl p-6">
          <h3 className="font-semibold text-lg mb-1">Upload a document →</h3>
          <p className="text-slate-500 text-sm">Add PDFs to power document-grounded Q&A with citations.</p>
        </Link>
      </div>
    </div>
  );
}
