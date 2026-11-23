import React, { useState, useEffect, useRef } from 'react';
import {
  Phone,
  PhoneOff,
  Mic,
  MicOff,
  Volume2,
  Send,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  User,
  ShieldCheck,
  X,
  ChevronDown
} from 'lucide-react';
import AudioWaveform from './AudioWaveform';

export default function PhoneModal({
  isOpen,
  onClose,
  callState, // 'idle', 'ringing', 'connected', 'ended'
  callDuration,
  isMuted,
  onToggleMute,
  onEndCall,
  onStartCall,
  transcript,
  isBotSpeaking,
  isUserSpeaking,
  onSendMessage,
  activeBookingNotification,
  verifiedPhone,
}) {
  const [inputText, setInputText] = useState('');
  const transcriptEndRef = useRef(null);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  if (!isOpen) return null;

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSend = (e) => {
    e?.preventDefault();
    if (!inputText.trim()) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const sendQuickPhrase = (phrase) => {
    onSendMessage(phrase);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-fade-in">
      {/* Smartphone Casing */}
      <div className="relative w-full max-w-[390px] h-[780px] max-h-[92vh] bg-slate-900 rounded-[48px] p-3 shadow-2xl border-4 border-slate-700/60 flex flex-col overflow-hidden ring-1 ring-white/10">
        
        {/* Dynamic Island / Notch */}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 w-28 h-5 bg-black rounded-full z-20 flex items-center justify-between px-3">
          <div className="w-2.5 h-2.5 rounded-full bg-slate-800 border border-slate-700"></div>
          <div className="w-2 h-2 rounded-full bg-emerald-500/80 animate-pulse"></div>
        </div>

        {/* Screen Bezel & Screen Inner */}
        <div className="w-full h-full bg-slate-950 rounded-[38px] flex flex-col overflow-hidden relative border border-slate-800">
          
          {/* Top Status Bar */}
          <div className="flex items-center justify-between px-6 pt-3 pb-2 text-[12px] text-slate-400 font-medium z-10">
            <span>{callState === 'connected' ? formatTimer(callDuration) : '9:41'}</span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-semibold tracking-wider text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded-full border border-emerald-800/40">
                HD Voice
              </span>
              <button
                onClick={onClose}
                className="w-5 h-5 rounded-full bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-300 transition-colors"
                title="Minimize Phone"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </div>

          {/* Caller / Clinic Info Header */}
          <div className="flex flex-col items-center px-6 pt-2 pb-3 border-b border-slate-800/60 bg-gradient-to-b from-slate-900/60 to-transparent">
            <div className="relative mb-2">
              <div className={`w-16 h-16 rounded-full bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center text-white shadow-lg ${callState === 'ringing' ? 'animate-bounce' : ''}`}>
                <Phone className="w-7 h-7" />
              </div>
              {callState === 'connected' && (
                <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-emerald-500 border-2 border-slate-950 flex items-center justify-center">
                  <ShieldCheck className="w-3 h-3 text-white" />
                </div>
              )}
            </div>

            <h3 className="text-white font-semibold text-base tracking-tight">
              Apex Health Medical
            </h3>
            
            <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
              {callState === 'ringing' && (
                <span className="text-amber-400 font-medium animate-pulse">Ringing receptionist...</span>
              )}
              {callState === 'connected' && (
                <span className="text-emerald-400 font-medium flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Active Call • {formatTimer(callDuration)}
                </span>
              )}
              {callState === 'ended' && (
                <span className="text-slate-400">Call Ended</span>
              )}
            </p>

            {/* Caller Identification rule badge */}
            <div className="mt-2 text-[11px] bg-slate-900 px-3 py-1 rounded-full text-slate-300 border border-slate-800 flex items-center gap-1.5">
              <User className="w-3 h-3 text-emerald-400" />
              <span>Caller Phone:</span>
              <span className="font-mono font-medium text-emerald-300">
                {verifiedPhone ? verifiedPhone : 'Identified by spoken voice'}
              </span>
            </div>

            {/* Live Audio Reactive Waveform */}
            <div className="w-full mt-1">
              <AudioWaveform
                isActive={callState === 'connected'}
                isBotSpeaking={isBotSpeaking}
                isUserSpeaking={isUserSpeaking}
              />
            </div>
          </div>

          {/* Transcript Scroll Area */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2.5 text-xs">
            {/* In-Phone Booking Confirmation Card (Bonus Feature) */}
            {activeBookingNotification && (
              <div className="p-3 rounded-2xl bg-gradient-to-br from-emerald-950/80 to-teal-950/80 border border-emerald-500/30 text-white shadow-xl animate-fade-in my-2">
                <div className="flex items-center gap-2 text-emerald-400 font-semibold mb-1">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>
                    {activeBookingNotification.action === 'book' ? 'Appointment Confirmed!' : 'Appointment Cancelled'}
                  </span>
                </div>
                <div className="text-[11px] text-slate-300 space-y-0.5">
                  <p className="font-medium text-white">{activeBookingNotification.appointment?.doctor_name}</p>
                  <p className="text-slate-400">{activeBookingNotification.appointment?.date} at {activeBookingNotification.appointment?.time_slot}</p>
                  <p className="text-[10px] text-emerald-300 font-mono mt-1">
                    ID: {activeBookingNotification.appointment?.appointment_id} • Phone: {activeBookingNotification.appointment?.caller_phone}
                  </p>
                </div>
              </div>
            )}

            {transcript.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 p-4">
                <Sparkles className="w-8 h-8 text-slate-600 mb-2" />
                <p className="text-xs font-medium text-slate-400">Voice Pipeline Ready</p>
                <p className="text-[11px] text-slate-500 mt-1">
                  Speak into your microphone or pick a quick phrase below.
                </p>
              </div>
            ) : (
              transcript.map((msg, index) => (
                <div
                  key={index}
                  className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div className="flex items-center gap-1 mb-0.5 text-[10px] text-slate-400 font-medium px-1">
                    <span>{msg.role === 'user' ? 'You (Caller)' : 'AI Receptionist'}</span>
                  </div>
                  <div
                    className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl leading-relaxed shadow-sm ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white rounded-tr-none'
                        : 'bg-slate-800 text-slate-100 rounded-tl-none border border-slate-700/50'
                    }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))
            )}
            <div ref={transcriptEndRef} />
          </div>

          {/* Quick Speak Shortcuts */}
          {callState === 'connected' && (
            <div className="px-3 py-1 bg-slate-900/80 border-t border-slate-800 flex gap-1.5 overflow-x-auto no-scrollbar text-[11px]">
              <button
                onClick={() => sendQuickPhrase("Is Dr. Sarah Jenkins available today?")}
                className="whitespace-nowrap px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              >
                🩺 Check Dr. Jenkins
              </button>
              <button
                onClick={() => sendQuickPhrase("I want to book an appointment for 10:30 AM")}
                className="whitespace-nowrap px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              >
                📅 Book 10:30 AM
              </button>
              <button
                onClick={() => sendQuickPhrase("My phone number is 9876543210")}
                className="whitespace-nowrap px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              >
                📱 Give Phone Number
              </button>
              <button
                onClick={() => sendQuickPhrase("Yes, that is correct")}
                className="whitespace-nowrap px-2.5 py-1 rounded-full bg-emerald-900/60 hover:bg-emerald-800/80 text-emerald-200 border border-emerald-700 transition"
              >
                ✅ Confirm Number
              </button>
              <button
                onClick={() => sendQuickPhrase("I need to cancel my appointment")}
                className="whitespace-nowrap px-2.5 py-1 rounded-full bg-rose-900/60 hover:bg-rose-800/80 text-rose-200 border border-rose-700 transition"
              >
                ❌ Cancel Appointment
              </button>
            </div>
          )}

          {/* Text Input Fallback Bar inside phone */}
          {callState === 'connected' && (
            <form onSubmit={handleSend} className="px-3 py-2 bg-slate-950 border-t border-slate-800/80 flex items-center gap-1.5">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Speak into mic or type here..."
                className="flex-1 bg-slate-900 text-slate-100 placeholder-slate-500 text-xs px-3 py-2 rounded-xl border border-slate-800 focus:outline-none focus:border-emerald-500"
              />
              <button
                type="submit"
                disabled={!inputText.trim()}
                className="w-8 h-8 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white flex items-center justify-center transition-all"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          )}

          {/* Bottom Call Action Buttons */}
          <div className="p-4 bg-slate-900/90 border-t border-slate-800/80 flex items-center justify-around">
            {callState === 'connected' ? (
              <>
                {/* Mute Mic Button */}
                <button
                  onClick={onToggleMute}
                  className={`w-12 h-12 rounded-full flex flex-col items-center justify-center transition-all ${
                    isMuted
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50'
                      : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                  }`}
                  title={isMuted ? 'Unmute Microphone' : 'Mute Microphone'}
                >
                  {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </button>

                {/* Hang up Red Button */}
                <button
                  onClick={onEndCall}
                  className="w-16 h-16 rounded-full bg-rose-600 hover:bg-rose-500 text-white flex items-center justify-center shadow-lg shadow-rose-900/40 hover:scale-105 active:scale-95 transition-all"
                  title="End Call"
                >
                  <PhoneOff className="w-7 h-7" />
                </button>

                {/* Volume / Speaker Info */}
                <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center">
                  <Volume2 className="w-5 h-5" />
                </div>
              </>
            ) : callState === 'ringing' ? (
              <button
                onClick={onEndCall}
                className="w-16 h-16 rounded-full bg-rose-600 hover:bg-rose-500 text-white flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all"
                title="Cancel Call"
              >
                <PhoneOff className="w-7 h-7" />
              </button>
            ) : (
              <button
                onClick={onStartCall}
                className="w-full py-3.5 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium flex items-center justify-center gap-2 shadow-lg transition"
              >
                <Phone className="w-5 h-5" />
                <span>Start Call</span>
              </button>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
