"use client";

import { useEffect, useState, useCallback } from "react";
import { listDocuments, uploadDocument, DocumentItem } from "@/lib/api";
import { UploadCloud, FileText, CheckCircle2, XCircle, Loader2 } from "lucide-react";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    listDocuments().then(setDocs).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleFile(file: File) {
    setError(null);
    setUploading(true);
    try {
      await uploadDocument(file);
      refresh();
    } catch (e: any) {
      setError(e.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Documents</h1>
      <p className="text-slate-500 mb-6">Upload PDFs to power the Document Intelligence Agent's RAG pipeline.</p>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files?.[0];
          if (file) handleFile(file);
        }}
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors mb-8 ${
          dragOver ? "border-brand-500 bg-brand-50" : "border-slate-300 bg-white"
        }`}
      >
        {uploading ? (
          <Loader2 className="mx-auto mb-3 animate-spin text-brand-600" size={28} />
        ) : (
          <UploadCloud className="mx-auto mb-3 text-slate-400" size={28} />
        )}
        <p className="text-sm text-slate-600 mb-2">Drag & drop a PDF here, or</p>
        <label className="inline-block bg-brand-600 hover:bg-brand-700 text-white text-sm px-4 py-2 rounded-lg cursor-pointer">
          Browse files
          <input
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
        </label>
        {error && <p className="text-rose-600 text-xs mt-3">{error}</p>}
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th className="px-4 py-3 font-medium">Filename</th>
              <th className="px-4 py-3 font-medium">Pages</th>
              <th className="px-4 py-3 font-medium">Chunks</th>
              <th className="px-4 py-3 font-medium">Size</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {docs.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-400">No documents uploaded yet.</td></tr>
            )}
            {docs.map((d) => (
              <tr key={d.id} className="border-t border-slate-100">
                <td className="px-4 py-3 flex items-center gap-2"><FileText size={14} className="text-slate-400" /> {d.filename}</td>
                <td className="px-4 py-3">{d.num_pages}</td>
                <td className="px-4 py-3">{d.num_chunks}</td>
                <td className="px-4 py-3">{(d.size_bytes / 1024).toFixed(1)} KB</td>
                <td className="px-4 py-3">
                  {d.status === "READY" ? (
                    <span className="inline-flex items-center gap-1 text-emerald-600"><CheckCircle2 size={14} /> Ready</span>
                  ) : d.status === "FAILED" ? (
                    <span className="inline-flex items-center gap-1 text-rose-600"><XCircle size={14} /> Failed</span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-amber-600"><Loader2 size={14} className="animate-spin" /> Processing</span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-400">{new Date(d.uploaded_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
