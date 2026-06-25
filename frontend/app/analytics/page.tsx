"use client";

import { useEffect, useState } from "react";
import { getAnalytics, AnalyticsSummary } from "@/lib/api";
import { MessageSquare, Calendar, Users, FileText, Clock, Bot } from "lucide-react";

const AGENT_LABELS: Record<string, string> = {
  document_agent: "Document Agent",
  appointment_agent: "Appointment Agent",
  memory_agent: "Memory Agent",
};

export default function AnalyticsPage() {
  const [stats, setStats] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    getAnalytics().then(setStats).catch(() => {});
    const interval = setInterval(() => {
      getAnalytics().then(setStats).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const maxUsage = stats ? Math.max(1, ...Object.values(stats.agent_usage)) : 1;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Analytics</h1>
      <p className="text-slate-500 mb-6">Live platform usage and agent execution metrics (auto-refreshes every 5s).</p>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        {[
          { label: "Total Chats", value: stats?.total_chats, icon: MessageSquare },
          { label: "Appointments", value: stats?.total_appointments, icon: Calendar },
          { label: "Users", value: stats?.total_users, icon: Users },
          { label: "Documents", value: stats?.total_documents, icon: FileText },
          { label: "Avg Response", value: stats ? `${stats.avg_response_time_ms.toFixed(0)}ms` : undefined, icon: Clock },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="bg-white border border-slate-200 rounded-xl p-4">
            <Icon size={16} className="text-brand-600 mb-2" />
            <p className="text-xl font-semibold">{value ?? "—"}</p>
            <p className="text-xs text-slate-500">{label}</p>
          </div>
        ))}
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6">
        <h3 className="font-semibold mb-4 flex items-center gap-2"><Bot size={16} /> Agent Utilization</h3>
        <div className="space-y-3">
          {stats && Object.entries(stats.agent_usage).length > 0 ? (
            Object.entries(stats.agent_usage).map(([agent, count]) => (
              <div key={agent}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium">{AGENT_LABELS[agent] || agent}</span>
                  <span className="text-slate-400">{count} calls</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-2 bg-brand-600 rounded-full"
                    style={{ width: `${(count / maxUsage) * 100}%` }}
                  />
                </div>
              </div>
            ))
          ) : (
            <p className="text-slate-400 text-sm">No agent activity yet. Start a chat to see usage data.</p>
          )}
        </div>
      </div>
    </div>
  );
}
