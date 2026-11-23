import React, { useState, useEffect, useRef } from 'react';
import {
  Phone,
  PhoneCall,
  Calendar,
  Clock,
  User,
  ShieldCheck,
  Stethoscope,
  RefreshCw,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Activity,
  Layers,
  ChevronRight,
  Headphones,
  Sliders
} from 'lucide-react';
import PhoneModal from './components/PhoneModal';
import DoctorCard from './components/DoctorCard';
import AppointmentsTable from './components/AppointmentsTable';
import { sounds } from './utils/audio';

export default function App() {
  // Clinic & Dashboard State
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [targetDate, setTargetDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });
  const [selectedSpecialty, setSelectedSpecialty] = useState('All');
  const [config, setConfig] = useState({
    gemini_configured: false,
    elevenlabs_configured: false,
    mode: 'local_interactive',
    gemini_model: 'gemini-2.0-flash',
  });
  const [highlightedAptId, setHighlightedAptId] = useState(null);
  const [activeBookingNotification, setActiveBookingNotification] = useState(null);
  const [verifiedPhone, setVerifiedPhone] = useState(null);

  // Call & Voice State
  const [isPhoneModalOpen, setIsPhoneModalOpen] = useState(false);
  const [callState, setCallState] = useState('idle'); // idle, ringing, connected, ended
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [isBotSpeaking, setIsBotSpeaking] = useState(false);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);

  // Refs
  const wsRef = useRef(null);
  const timerRef = useRef(null);
  const recognitionRef = useRef(null);
  const isCallActiveRef = useRef(false);

  // Fetch initial data
  const fetchData = async () => {
    try {
      const [docRes, aptRes, cfgRes] = await Promise.all([
        fetch('/api/doctors'),
        fetch('/api/appointments'),
        fetch('/api/config')
      ]);
      const docs = await docRes.json();
      const apts = await aptRes.json();
      const cfg = await cfgRes.json();

      setDoctors(docs);
      setAppointments(apts);
      setConfig(cfg);
    } catch (e) {
      console.error('Failed to load clinic data:', e);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Call timer effect
  useEffect(() => {
    if (callState === 'connected') {
      timerRef.current = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [callState]);

  // Speech Recognition Setup (Web Speech API)
  const initSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return null;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsUserSpeaking(true);
    };

    recognition.onresult = (event) => {
      const last = event.results.length - 1;
      const text = event.results[last][0].transcript.trim();
      if (text && isCallActiveRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        setIsUserSpeaking(false);
        wsRef.current.send(JSON.stringify({
          type: 'user_speech',
          text: text
        }));
      }
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition notice:', event.error);
      setIsUserSpeaking(false);
    };

    recognition.onend = () => {
      if (isCallActiveRef.current && !isMuted) {
        try {
          recognition.start();
        } catch (e) {}
      } else {
        setIsUserSpeaking(false);
      }
    };

    return recognition;
  };

  // Start Voice Call
  const handleStartCall = () => {
    setIsPhoneModalOpen(true);
    setCallState('ringing');
    setCallDuration(0);
    setTranscript([]);
    setVerifiedPhone(null);
    setActiveBookingNotification(null);
    isCallActiveRef.current = true;

    // Play ringing sound
    sounds.startRinging();

    // Establish WebSocket Connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/call`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      // Transition from ringing to connected after 2.5s for realistic phone call experience
      setTimeout(() => {
        if (!isCallActiveRef.current) return;
        sounds.playConnectChime();
        setCallState('connected');

        // Start listening via microphone
        const rec = initSpeechRecognition();
        if (rec) {
          recognitionRef.current = rec;
          try {
            rec.start();
          } catch (e) {
            console.warn('Could not auto-start speech recognition:', e);
          }
        }
      }, 2500);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        if (msg.type === 'transcript') {
          setTranscript((prev) => [...prev, {
            role: msg.role,
            text: msg.text,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }]);

          // Synthesize AI speech if assistant and in browser
          if (msg.role === 'assistant') {
            setIsBotSpeaking(true);
            if ('speechSynthesis' in window) {
              window.speechSynthesis.cancel();
              const utterance = new SpeechSynthesisUtterance(msg.text);
              utterance.rate = 1.05;
              utterance.pitch = 1.0;
              utterance.onend = () => setIsBotSpeaking(false);
              utterance.onerror = () => setIsBotSpeaking(false);
              window.speechSynthesis.speak(utterance);
            } else {
              setTimeout(() => setIsBotSpeaking(false), 2000);
            }
          }
        } else if (msg.type === 'appointment_updated') {
          // Real-time update from tool execution
          fetchData();
          const apt = msg.data?.appointment;
          if (apt) {
            setHighlightedAptId(apt.appointment_id);
            setActiveBookingNotification(msg.data);
            if (apt.caller_phone) {
              setVerifiedPhone(apt.caller_phone);
            }
            setTimeout(() => setHighlightedAptId(null), 4000);
          }
        } else if (msg.type === 'tool_call_result') {
          if (msg.function_name === 'phone_confirmation_requested' && msg.result?.phone) {
            setVerifiedPhone(msg.result.phone);
          }
        }
      } catch (err) {
        console.warn('WS message parse error:', err);
      }
    };

    ws.onclose = () => {
      handleEndCall();
    };

    ws.onerror = (err) => {
      console.error('WS error:', err);
      handleEndCall();
    };
  };

  // End Voice Call
  const handleEndCall = () => {
    isCallActiveRef.current = false;
    sounds.playEndCallBeep();
    setCallState('ended');
    setIsBotSpeaking(false);
    setIsUserSpeaking(false);

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      recognitionRef.current = null;
    }

    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'end_call' }));
        wsRef.current.close();
      }
      wsRef.current = null;
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  };

  // Toggle Mute
  const handleToggleMute = () => {
    if (isMuted) {
      setIsMuted(false);
      try {
        recognitionRef.current?.start();
      } catch (e) {}
    } else {
      setIsMuted(true);
      try {
        recognitionRef.current?.stop();
      } catch (e) {}
    }
  };

  // Send message from phone UI
  const handleSendMessage = (text) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'user_text',
        text: text
      }));
    }
  };

  // Manual cancel test from table
  const handleCancelAppointment = async (phone, aptId) => {
    try {
      const res = await fetch('/api/appointments/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phone, appointment_id: aptId })
      });
      const data = await res.json();
      if (data.status === 'success') {
        fetchData();
        setHighlightedAptId(aptId);
        setTimeout(() => setHighlightedAptId(null), 3000);
      }
    } catch (e) {
      console.error('Cancel appointment error:', e);
    }
  };

  // Reset Data
  const handleResetData = async () => {
    try {
      await fetch('/api/reset', { method: 'POST' });
      fetchData();
    } catch (e) {
      console.error('Reset error:', e);
    }
  };

  // Specialties list
  const specialties = ['All', 'Cardiology', 'Dermatology', 'Pediatrics', 'General Medicine', 'Orthopedics'];

  const filteredDoctors = doctors.filter((doc) => {
    if (selectedSpecialty === 'All') return true;
    return doc.specialty.toLowerCase() === selectedSpecialty.toLowerCase();
  });

  // Calculate booked slots for doctors on target date
  const getBookedSlotsForDoctor = (docId) => {
    return appointments
      .filter((a) => a.doctor_id === docId && a.date === targetDate && a.status === 'CONFIRMED')
      .map((a) => a.time_slot);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-800">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-600/20">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base text-slate-900 tracking-tight">Apex Health</span>
                <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Voice AI
                </span>
              </div>
              <p className="text-[11px] text-slate-500">Autonomous Doctor Appointment Assistant</p>
            </div>
          </div>

          {/* Center Pipeline Tech Tag */}
          <div className="hidden md:flex items-center gap-2 text-xs bg-slate-100/80 px-3 py-1.5 rounded-full border border-slate-200/60 text-slate-600">
            <Activity className="w-3.5 h-3.5 text-emerald-600 animate-pulse" />
            <span>Pipecat</span>
            <span className="text-slate-300">•</span>
            <span>ElevenLabs STT/TTS</span>
            <span className="text-slate-300">•</span>
            <span>Gemini LLM</span>
            <span className="text-slate-300">•</span>
            <span>Silero VAD</span>
          </div>

          {/* Action CTAs */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleResetData}
              className="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
              title="Reset Database to Seed State"
            >
              <RefreshCw className="w-4 h-4" />
            </button>

            {/* Primary "Try Call" Button */}
            <button
              onClick={handleStartCall}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-semibold text-xs flex items-center gap-2 shadow-md shadow-emerald-600/25 transition-all"
            >
              <PhoneCall className="w-4 h-4 animate-bounce" />
              <span>Try Call</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Dashboard Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Banner with SDE Internship Specs alignment */}
        <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-emerald-950 p-6 text-white shadow-xl relative overflow-hidden">
          <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-radial from-emerald-500/10 to-transparent pointer-events-none"></div>
          <div className="max-w-2xl relative z-10">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-[11px] font-semibold border border-emerald-500/30 mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              SDE Intern - Round 1 Voice AI Assistant
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Real-Time Voice Receptionist Pipeline
            </h1>
            <p className="text-slate-300 text-xs sm:text-sm mt-1.5 leading-relaxed">
              Caller speaks to check availability, book, or cancel. Identified <strong className="text-emerald-300">only by phone number</strong> spoken out loud with required read-back confirmation. All slots and appointments sync in real time.
            </p>
            <div className="flex flex-wrap items-center gap-3 mt-4">
              <button
                onClick={handleStartCall}
                className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center gap-2 shadow-md transition"
              >
                <Phone className="w-3.5 h-3.5" />
                Launch Voice Call Interface
              </button>
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Zero login • Zero OTP • Spoken Phone Identification</span>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="text-xs text-slate-500 font-medium">Available Doctors</div>
            <div className="text-2xl font-bold text-slate-900 mt-1">{doctors.length}</div>
            <div className="text-[11px] text-emerald-600 mt-0.5">Cardiology, Dermatology & more</div>
          </div>
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="text-xs text-slate-500 font-medium">Date Selected</div>
            <div className="text-sm font-bold text-slate-900 mt-1 font-mono">{targetDate}</div>
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="text-[11px] text-slate-600 font-medium mt-1 cursor-pointer bg-slate-50 px-2 py-0.5 rounded-lg border border-slate-200"
            />
          </div>
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="text-xs text-slate-500 font-medium">Active Bookings</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">
              {appointments.filter(a => a.status === 'CONFIRMED').length}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Confirmed appointments</div>
          </div>
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="text-xs text-slate-500 font-medium">Cancelled Bookings</div>
            <div className="text-2xl font-bold text-rose-600 mt-1">
              {appointments.filter(a => a.status === 'CANCELLED').length}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Freed back to open slots</div>
          </div>
        </div>

        {/* Doctor Availability Section */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Doctors & Available Time Slots
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Slots turn strikethrough gray when booked and green when available
              </p>
            </div>

            {/* Specialty Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 no-scrollbar">
              {specialties.map((spec) => (
                <button
                  key={spec}
                  onClick={() => setSelectedSpecialty(spec)}
                  className={`text-xs px-3 py-1.5 rounded-full font-medium whitespace-nowrap transition-all ${
                    selectedSpecialty === spec
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {spec}
                </button>
              ))}
            </div>
          </div>

          {/* Doctors Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredDoctors.map((doc) => (
              <DoctorCard
                key={doc.id}
                doctor={doc}
                targetDate={targetDate}
                bookedSlots={getBookedSlotsForDoctor(doc.id)}
              />
            ))}
          </div>
        </section>

        {/* Live Appointments Table Section */}
        <section className="space-y-4">
          <AppointmentsTable
            appointments={appointments}
            highlightedAptId={highlightedAptId}
            onCancelAppointment={handleCancelAppointment}
          />
        </section>

      </main>

      {/* Floating CTA to launch call if modal is closed */}
      {!isPhoneModalOpen && (
        <div className="fixed bottom-6 right-6 z-30">
          <button
            onClick={handleStartCall}
            className="flex items-center gap-2.5 px-5 py-3.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-xl shadow-emerald-900/30 hover:scale-105 active:scale-95 transition-all ring-4 ring-emerald-500/20"
          >
            <PhoneCall className="w-5 h-5 animate-pulse" />
            <span>Try Voice Assistant</span>
          </button>
        </div>
      )}

      {/* Phone-Style Call Screen Modal */}
      <PhoneModal
        isOpen={isPhoneModalOpen}
        onClose={() => setIsPhoneModalOpen(false)}
        callState={callState}
        callDuration={callDuration}
        isMuted={isMuted}
        onToggleMute={handleToggleMute}
        onEndCall={handleEndCall}
        onStartCall={handleStartCall}
        transcript={transcript}
        isBotSpeaking={isBotSpeaking}
        isUserSpeaking={isUserSpeaking}
        onSendMessage={handleSendMessage}
        activeBookingNotification={activeBookingNotification}
        verifiedPhone={verifiedPhone}
      />
    </div>
  );
}
