"use client";

import { useEffect, useState } from "react";
import { listAppointments, AppointmentItem } from "@/lib/api";
import { Calendar, Mail, Phone } from "lucide-react";

export default function AppointmentsPage() {
  const [appts, setAppts] = useState<AppointmentItem[]>([]);

  useEffect(() => {
    listAppointments().then(setAppts).catch(() => {});
  }, []);

  const byDate = [...appts].sort((a, b) => a.appointment_date.localeCompare(b.appointment_date));

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Appointments</h1>
      <p className="text-slate-500 mb-6">Bookings collected by the Appointment Agent's conversational state machine.</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
        {byDate.slice(0, 6).map((a) => (
          <div key={a.id} className="bg-white border border-slate-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-brand-600 mb-2">
              <Calendar size={15} />
              <span className="text-sm font-semibold">{a.appointment_date}</span>
            </div>
            <p className="font-medium text-sm">{a.full_name}</p>
            <p className="text-xs text-slate-400 flex items-center gap-1 mt-1"><Mail size={11} /> {a.email}</p>
            <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5"><Phone size={11} /> {a.phone}</p>
            <span className="inline-block mt-3 text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
              {a.status}
            </span>
          </div>
        ))}
        {byDate.length === 0 && <p className="text-slate-400 text-sm col-span-3">No appointments booked yet.</p>}
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Phone</th>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Original Input</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Booked At</th>
            </tr>
          </thead>
          <tbody>
            {appts.map((a) => (
              <tr key={a.id} className="border-t border-slate-100">
                <td className="px-4 py-3">{a.full_name}</td>
                <td className="px-4 py-3 text-slate-500">{a.email}</td>
                <td className="px-4 py-3 text-slate-500">{a.phone}</td>
                <td className="px-4 py-3 font-medium">{a.appointment_date}</td>
                <td className="px-4 py-3 text-slate-400 italic">"{a.original_date_text}"</td>
                <td className="px-4 py-3"><span className="text-emerald-600 text-xs font-medium">{a.status}</span></td>
                <td className="px-4 py-3 text-slate-400">{new Date(a.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
