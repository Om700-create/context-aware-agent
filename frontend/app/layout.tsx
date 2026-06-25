import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "ContextAI — Multi-Agent Conversational Platform",
  description: "Context-aware document Q&A and appointment booking, powered by a multi-agent LangGraph backend.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex">
        <Sidebar />
        <main className="flex-1 min-h-screen">{children}</main>
      </body>
    </html>
  );
}
