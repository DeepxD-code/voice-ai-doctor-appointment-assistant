import React from 'react';
import { Calendar, Clock, Award, DollarSign, CheckCircle2 } from 'lucide-react';

export default function DoctorCard({ doctor, targetDate, bookedSlots = [] }) {
  const allSlots = doctor.slots || [];
  const bookedSet = new Set(bookedSlots);

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between">
      <div>
        {/* Doctor Header */}
        <div className="flex items-start gap-4 mb-3">
          <img
            src={doctor.avatar}
            alt={doctor.name}
            className="w-16 h-16 rounded-2xl object-cover ring-2 ring-emerald-500/20 shadow-sm"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60">
                {doctor.specialty}
              </span>
              <span className="text-xs text-slate-400 font-medium">
                {doctor.experience_years}y exp
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-900 mt-1 truncate">
              {doctor.name}
            </h3>
            <p className="text-xs text-slate-500 truncate">
              {doctor.qualification}
            </p>
          </div>
        </div>

        {/* Schedule & Fee meta */}
        <div className="flex items-center justify-between py-2 border-y border-slate-100 text-xs text-slate-600 mb-3">
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span className="truncate max-w-[170px]">
              {(doctor.available_days || []).join(', ')}
            </span>
          </div>
          <div className="font-semibold text-slate-800">
            ${doctor.consultation_fee}
          </div>
        </div>

        {/* Available Time Slots */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-700 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-emerald-600" />
              Available Slots ({targetDate}):
            </span>
            <span className="text-[11px] font-medium text-emerald-600">
              {allSlots.filter(s => !bookedSet.has(s)).length} open
            </span>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {allSlots.map((slot, idx) => {
              const isBooked = bookedSet.has(slot);
              return (
                <span
                  key={idx}
                  className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-all ${
                    isBooked
                      ? 'bg-slate-100 text-slate-400 line-through border border-slate-200 cursor-not-allowed'
                      : 'bg-emerald-50 text-emerald-800 border border-emerald-200/80 hover:bg-emerald-100'
                  }`}
                  title={isBooked ? 'Slot already booked' : 'Slot available for booking'}
                >
                  {slot}
                </span>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
