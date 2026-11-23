"""
Generates the complete synchronized soundtrack for the demo video:
- Phone ringing tone
- Connect chime
- Spoken dialogue between Caller (en-US-GuyNeural) and AI Receptionist (en-US-JennyNeural)
- Disconnect beeps
"""

import asyncio
import os
import numpy as np
import soundfile as sf
import edge_tts

SAMPLE_RATE = 24000

def generate_tone(freqs, duration, volume=0.15):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    signal = np.zeros_like(t)
    for f in freqs:
        signal += volume * np.sin(2 * np.pi * f * t)
    # 20ms fade in/out
    fade = int(SAMPLE_RATE * 0.02)
    if len(signal) > fade * 2:
        signal[:fade] *= np.linspace(0, 1, fade)
        signal[-fade:] *= np.linspace(1, 0, fade)
    return signal

def generate_silence(duration):
    return np.zeros(int(SAMPLE_RATE * duration))

async def synthesize_speech(text, voice, out_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)

def load_audio_as_float(file_path):
    data, sr = sf.read(file_path)
    if sr != SAMPLE_RATE:
        # Simple resample or reload via ffmpeg
        import subprocess
        tmp_wav = file_path.replace(".mp3", "_resampled.wav")
        subprocess.run([
            "ffmpeg", "-y", "-i", file_path, "-ar", str(SAMPLE_RATE), "-ac", "1", tmp_wav
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        data, _ = sf.read(tmp_wav)
        try: os.remove(tmp_wav)
        except Exception: pass
    if len(data.shape) > 1:
        data = data.mean(axis=1)
    return data.astype(np.float32)

async def build_soundtrack():
    os.makedirs("audio_clips", exist_ok=True)
    voice_ai = "en-US-JennyNeural"
    voice_caller = "en-US-GuyNeural"

    script = [
        # (id, role, text)
        ("ai_1", voice_ai, "Hello! Thank you for calling Apex Health Medical Center. I can check doctor availability, book appointments, or cancel existing ones. How can I assist you today?"),
        ("caller_1", voice_caller, "Is Doctor Sarah Jenkins available today?"),
        ("ai_2", voice_ai, "Doctor Sarah Jenkins in Cardiology has available slots: 10:30 AM, 2:00 PM, and 3:30 PM. Which one would suit you best?"),
        ("caller_2", voice_caller, "I would like to book the 10:30 AM slot please."),
        ("ai_3", voice_ai, "I would be glad to book 10:30 AM with Doctor Jenkins. May I please have your phone number to reserve the slot?"),
        ("caller_3", voice_caller, "My phone number is 9 8 7 6 5 4 3 2 1 0."),
        ("ai_4", voice_ai, "Just to confirm, I have your phone number as 9 8 7 6 5 4 3 2 1 0. Is that correct?"),
        ("caller_4", voice_caller, "Yes, that is correct."),
        ("ai_5", voice_ai, "Thank you! Your appointment with Doctor Sarah Jenkins has been confirmed for today at 10:30 AM. Your appointment ID is APT-2841. Is there anything else I can help you with?"),
        ("caller_5", voice_caller, "Actually, I also need to cancel an existing appointment."),
        ("ai_6", voice_ai, "I can certainly help you cancel your appointment. May I please have the phone number you used when booking?"),
        ("caller_6", voice_caller, "It is 9 8 7 6 5 4 3 2 1 0."),
        ("ai_7", voice_ai, "Just to confirm, I have your phone number as 9 8 7 6 5 4 3 2 1 0. Shall I proceed with cancelling your appointment?"),
        ("caller_7", voice_caller, "Yes, please cancel it."),
        ("ai_8", voice_ai, "Your appointment has been successfully cancelled. Can I help you with anything else?"),
        ("caller_8", voice_caller, "No, that's everything. Thank you so much, goodbye!"),
        ("ai_9", voice_ai, "You are welcome. Have a wonderful day!")
    ]

    print("Generating speech audio clips...")
    for clip_id, voice, text in script:
        path = os.path.join("audio_clips", f"{clip_id}.mp3")
        await synthesize_speech(text, voice, path)

    # Generate Sound Effects
    # 1. Ringing tone (dual tone 440 + 480 Hz for 1.8s)
    ring_burst = generate_tone([440, 480], 1.5, volume=0.10)
    ring_silence = generate_silence(0.8)
    full_ring = np.concatenate([ring_burst, ring_silence, ring_burst])

    # 2. Connect chime (C5 -> E5)
    t = np.linspace(0, 0.35, int(SAMPLE_RATE * 0.35), False)
    f = np.linspace(523.25, 659.25, len(t))
    connect_chime = 0.15 * np.sin(2 * np.pi * f * t) * np.linspace(1, 0, len(t))

    # 3. Disconnect beeps (480Hz three beeps)
    beep = generate_tone([480], 0.12, volume=0.12)
    beep_silence = generate_silence(0.10)
    disconnect_beeps = np.concatenate([beep, beep_silence, beep, beep_silence, beep])

    # Timeline layout:
    # 0.0s - 4.0s: App overview (gentle intro silence)
    # 4.0s - 7.5s: Telephone Ringing
    # 7.5s - 8.0s: Connect chime
    # 8.0s onwards: Dialogue sequence with natural 0.6s pauses
    audio_segments = [
        generate_silence(4.0),
        full_ring,
        connect_chime,
        generate_silence(0.5)
    ]

    time_markers = {}
    current_time = 4.0 + len(full_ring)/SAMPLE_RATE + 0.35 + 0.5

    for clip_id, voice, text in script:
        clip_path = os.path.join("audio_clips", f"{clip_id}.mp3")
        clip_data = load_audio_as_float(clip_path)
        time_markers[clip_id] = current_time
        audio_segments.append(clip_data)
        pause_dur = 0.8 if "caller" in clip_id else 0.7
        audio_segments.append(generate_silence(pause_dur))
        current_time += (len(clip_data) / SAMPLE_RATE) + pause_dur

    # Hangup beeps
    audio_segments.append(disconnect_beeps)
    audio_segments.append(generate_silence(5.0)) # Outro dashboard view

    soundtrack = np.concatenate(audio_segments)
    sf.write("full_soundtrack.wav", soundtrack, SAMPLE_RATE)
    total_sec = len(soundtrack) / SAMPLE_RATE
    print(f">> SUCCESS: full_soundtrack.wav generated! Total duration: {total_sec:.2f} seconds.")

    import json
    with open("audio_markers.json", "w") as f:
        json.dump(time_markers, f, indent=2)

if __name__ == "__main__":
    asyncio.run(build_soundtrack())
