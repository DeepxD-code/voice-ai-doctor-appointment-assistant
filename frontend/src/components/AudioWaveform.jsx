import React, { useEffect, useRef } from 'react';

export default function AudioWaveform({ isActive, isBotSpeaking, isUserSpeaking }) {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let phase = 0;
    const numBars = 32;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const width = canvas.width;
      const height = canvas.height;
      const centerY = height / 2;
      const barWidth = width / numBars - 2;

      for (let i = 0; i < numBars; i++) {
        let barHeight = 4;
        let color = 'rgba(148, 163, 184, 0.4)'; // slate-400 idle

        if (isActive) {
          if (isBotSpeaking) {
            // Flowing cyan/emerald waves for AI agent
            const wave = Math.sin(phase + i * 0.3) * 0.5 + 0.5;
            barHeight = 6 + wave * 32;
            color = `rgba(16, 185, 129, ${0.4 + wave * 0.6})`; // emerald
          } else if (isUserSpeaking) {
            // Dynamic blue/indigo ripples for caller
            const wave = Math.cos(phase * 1.5 + i * 0.4) * 0.5 + 0.5;
            barHeight = 8 + wave * 28;
            color = `rgba(59, 130, 246, ${0.4 + wave * 0.6})`; // blue
          } else {
            // Gentle ambient pulse while listening
            const wave = Math.sin(phase * 0.5 + i * 0.2) * 0.5 + 0.5;
            barHeight = 4 + wave * 8;
            color = 'rgba(99, 102, 241, 0.4)'; // indigo gentle
          }
        }

        const x = i * (barWidth + 2);
        const y = centerY - barHeight / 2;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, [2]);
        ctx.fill();
      }

      phase += 0.08;
      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isActive, isBotSpeaking, isUserSpeaking]);

  return (
    <div className="w-full flex flex-col items-center justify-center py-2">
      <canvas
        ref={canvasRef}
        width={240}
        height={48}
        className="w-full max-w-[240px] h-12 rounded-lg"
      />
      <div className="text-[11px] font-medium tracking-wide flex items-center gap-1.5 mt-1">
        {isBotSpeaking ? (
          <span className="text-emerald-500 font-semibold flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
            AI Assistant Speaking...
          </span>
        ) : isUserSpeaking ? (
          <span className="text-blue-500 font-semibold flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
            Listening to Caller...
          </span>
        ) : isActive ? (
          <span className="text-slate-400">Listening (VAD Active)</span>
        ) : (
          <span className="text-slate-400">Call Inactive</span>
        )}
      </div>
    </div>
  );
}
