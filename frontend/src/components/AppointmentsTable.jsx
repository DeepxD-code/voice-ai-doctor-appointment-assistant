import React, { useState } from 'react';
import { Calendar, Clock, Phone, User, CheckCircle2, XCircle, Search, Filter } from 'lucide-react';

export default function AppointmentsTable({ appointments, highlightedAptId, onCancelAppointment }) {
  const [filterPhone, setFilterPhone] = useState('');

  const formatPhone = (p) => {
    if (!p) return '';
    const digits = p.replace(/\D/g, '');
    if (digits.length === 10) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
    }
    return p;
  };

  const filtered = appointments.filter((apt) => {
    if (!filterPhone) return true;
    return (
      apt.caller_phone.includes(filterPhone) ||
      apt.doctor_name.toLowerCase().includes(filterPhone.toLowerCase()) ||
      apt.appointment_id.toLowerCase().includes(filterPhone.toLowerCase())
    );
  });

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
      {/* Header & Search */}
      <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-slate-900">
            Live Appointments Record
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Updated in real-time as the Voice AI agent books or cancels slots
          </p>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={filterPhone}
            onChange={(e) => setFilterPhone(e.target.value)}
            placeholder="Search phone, doctor, ID..."
            className="pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:bg-white transition"
          />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-50/70 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
              <th className="py-3 px-4">Appointment ID</th>
              <th className="py-3 px-4">Caller Phone</th>
              <th className="py-3 px-4">Doctor & Specialty</th>
              <th className="py-3 px-4">Date & Time</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                  No appointments found matching your search.
                </td>
              </tr>
            ) : (
              filtered.map((apt) => {
                const isHighlighted = apt.appointment_id === highlightedAptId;
                const isConfirmed = apt.status === 'CONFIRMED';

                return (
                  <tr
                    key={apt.id}
                    className={`transition-colors duration-500 ${
                      isHighlighted
                        ? 'bg-emerald-50/90 font-medium'
                        : 'hover:bg-slate-50/60'
                    }`}
                  >
                    {/* ID */}
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                      {apt.appointment_id}
                    </td>

                    {/* Caller Phone */}
                    <td className="py-3.5 px-4 text-slate-700">
                      <div className="flex items-center gap-1.5">
                        <Phone className="w-3.5 h-3.5 text-slate-400" />
                        <span className="font-mono font-medium">{formatPhone(apt.caller_phone)}</span>
                      </div>
                    </td>

                    {/* Doctor */}
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-900">{apt.doctor_name}</div>
                      <div className="text-[11px] text-slate-500">{apt.specialty}</div>
                    </td>

                    {/* Date & Time */}
                    <td className="py-3.5 px-4 text-slate-700">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>{apt.date}</span>
                      </div>
                      <div className="flex items-center gap-1 text-[11px] text-slate-500 mt-0.5">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>{apt.time_slot}</span>
                      </div>
                    </td>

                    {/* Status Badge */}
                    <td className="py-3.5 px-4">
                      {isConfirmed ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          Confirmed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                          <XCircle className="w-3 h-3 text-rose-500" />
                          Cancelled
                        </span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right">
                      {isConfirmed ? (
                        <button
                          onClick={() => onCancelAppointment(apt.caller_phone, apt.appointment_id)}
                          className="px-2.5 py-1 rounded-lg text-[11px] font-medium text-rose-600 hover:bg-rose-50 border border-rose-200 transition"
                        >
                          Cancel
                        </button>
                      ) : (
                        <span className="text-[11px] text-slate-400 italic">Inactive</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
