"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";

export default function SettingsPage() {
  const [apiBase] = useState(API_BASE);

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Settings</h1>
      <p className="text-slate-500 mb-6">Platform configuration (set via backend .env / frontend env vars).</p>

      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 text-sm">
        <div>
          <p className="text-slate-400 mb-1">API Base URL</p>
          <p className="font-mono bg-slate-50 px-3 py-2 rounded-lg">{apiBase}</p>
        </div>
        <div>
          <p className="text-slate-400 mb-1">LLM Provider</p>
          <p>Configured server-side via <code className="bg-slate-50 px-1.5 py-0.5 rounded">LLM_PROVIDER</code> in backend/.env (offline | ollama | openai).</p>
        </div>
        <div>
          <p className="text-slate-400 mb-1">Vector Store</p>
          <p>Local ChromaDB, persisted to <code className="bg-slate-50 px-1.5 py-0.5 rounded">backend/chroma_data</code>.</p>
        </div>
        <div>
          <p className="text-slate-400 mb-1">Database</p>
          <p>SQLite by default (<code className="bg-slate-50 px-1.5 py-0.5 rounded">backend/app.db</code>); swap <code className="bg-slate-50 px-1.5 py-0.5 rounded">DATABASE_URL</code> for Postgres in production.</p>
        </div>
      </div>
    </div>
  );
}
