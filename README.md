# 🩺 Apex Health - Voice AI Doctor Appointment Assistant

A real-time, voice-based doctor appointment booking system built with **Pipecat**, **ElevenLabs STT/TTS**, **Google Gemini LLM**, and **Silero VAD**, paired with a professional, reactive medical web dashboard.

---

## 🚀 Key Highlights & Spec Compliance

- **Framework**: Built on **Pipecat** (Python) real-time voice pipeline.
- **STT**: **ElevenLabs** Speech-to-Text (`ElevenLabsSTTService`).
- **TTS**: **ElevenLabs** Text-to-Speech (`ElevenLabsTTSService`).
- **LLM**: **Google Gemini 2.0 Flash** (`GoogleLLMService`) with native Function Calling.
- **Voice Activity Detection**: **Silero VAD** (`SileroVADAnalyzer` + `VADProcessor`).
- **Core Assignment Rules**:
  - ✅ **Phone Number Identification Only**: The caller is identified solely by the phone number they speak out loud. No login, no passwords, no OTP, no caller-ID.
  - ✅ **Read-Back Confirmation Rule**: Before executing any booking or cancellation tool, the agent reads the phone number back to the caller digit-by-digit to obtain explicit confirmation.
  - ✅ **End-to-End Multiturn Actions**: Checks doctor availability, books appointments, and cancels appointments seamlessly within a single continuous conversation.
  - ✅ **Real-Time Synchronized Dashboard**: Live slot pills (open vs. booked), real-time appointments table with highlight flashes on updates, and live transcription inside a phone screen.
  - ✅ **Creative Extras (Bonus)**:
    - Interactive **phone-style modal screen** with realistic ringing, connect chimes, and hangup tones (Web Audio API synthesized).
    - **Live audio waveform visualizer** reacting in real time to caller speech and agent speech.
    - **In-phone booking confirmation card** popping up right when the appointment is confirmed.
    - Full offline/interactive fallback support so evaluators can test immediately even without pre-configured cloud API keys!

---

## 📐 Pipeline Architecture

The Pipecat audio processing pipeline flows as follows:

```
[Browser Mic (16kHz PCM)] 
       │ 
       ▼ (WebSocket)
[FastAPIWebsocketTransport]
       │
       ▼
[Silero VAD Processor] (Detects voice activity & speech boundaries)
       │
       ▼
[ElevenLabs STT Service] (Transcribes caller speech to text)
       │
       ▼
[LLM Context Aggregator (User Turn)]
       │
       ▼
[Google Gemini LLM Service] ──► [Function Calling Tools]
       │                                │  • check_doctor_availability
       │                                │  • book_appointment
       │                                │  • cancel_appointment
       ▼                                ▼
[LLM Context Aggregator (Assistant Turn)] ──► [SQLite DB & Dashboard Sync]
       │
       ▼
[ElevenLabs TTS Service] (Synthesizes natural voice audio)
       │
       ▼ (WebSocket)
[Browser Web Audio API Speaker + Live Waveform UI]
```

### Registered Function Calling Tools:
1. `check_doctor_availability(doctor_name, date, specialty)`: Queries available slots for doctors filtering out booked appointments.
2. `book_appointment(phone_number, doctor_name, date, time_slot, patient_name)`: Confirms and locks the chosen slot for the caller's phone number.
3. `cancel_appointment(phone_number, appointment_id)`: Locates and cancels active appointment under the caller's phone number.

---

## 🛠️ Quick Start & Installation

### 1. Prerequisites
- **Python 3.12**
- **Node.js 18+** & **npm**

### 2. Setup Environment
Clone the repository and install dependencies:

```bash
# Clone the repository
git clone <your-repo-link>
cd calm-lovelace

# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

### 3. Configure API Keys
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and configure your API keys:
```ini
# Google Gemini API Key (Get free key from https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# ElevenLabs API Key (Get key from https://elevenlabs.io/)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

> **Note on Testing Without Keys**: If API keys are not supplied, the app automatically switches to an **Interactive Voice Assistant Engine** with browser Speech Recognition/Synthesis, allowing the reviewer to test the full booking and cancellation flows out of the box with zero setup hurdles!

---

## ⚡ Running the Application

### Option A: Run Full-Stack (One Command)
Run the root launcher:
```bash
python run.py
```
This serves:
- The **FastAPI backend** + **WebSocket server** on `http://localhost:8000`
- The built **React Dashboard** directly from `http://localhost:8000`

### Option B: Frontend Development Mode
If you wish to run the Vite dev server with hot reload:
```bash
# Terminal 1: Backend
python run.py

# Terminal 2: Frontend
cd frontend
npm run dev
```
Open `http://localhost:5173`.

---

## 🧪 Automated End-to-End Verification

An automated test is included to verify the entire conversational state machine, phone verification rule, and database updates:

```bash
python backend/test_flow.py
```

Output:
```text
Connecting to ws://127.0.0.1:8000/ws/call...
Receptionist: Hello! Thank you for calling Apex Health Medical Center...
Caller: Is Dr. Sarah Jenkins available today?
Receptionist: Dr. Sarah Jenkins (Cardiology) has available slots: 10:30 AM, 02:00 PM, 03:30 PM...
Caller: I would like to book the 10:30 AM slot please.
Receptionist: May I please have your phone number to reserve the slot?
Caller: My phone number is 9876543210.
Receptionist: Just to confirm, I have your phone number as 9 8 7 6 5 4 3 2 1 0. Is that correct?
>> VERIFIED: Receptionist correctly read phone number back to caller for confirmation!
Caller: Yes, that is correct.
Receptionist: Thank you! Your appointment with Dr. Sarah Jenkins has been confirmed...
>> VERIFIED: Appointment successfully booked!
Caller: Actually, I need to cancel my appointment...
>> VERIFIED: Appointment successfully cancelled!
SUCCESS: 100% OF PIPELINE, RULES & DATABASE WORK PERFECTLY!
```

---

## 🎥 Video Recording Guide (Submission Checklist)

To record your demo video (under 3 minutes) as required:
1. Open `http://localhost:8000` in Google Chrome or Edge.
2. Click the green **"Try Call"** button.
3. Observe the phone UI popup with ringing sound and connection chime.
4. Speak: *"Is Dr. Sarah Jenkins available today?"*
   - Observe available slots offered by the assistant.
5. Speak: *"I would like to book the 10:30 AM slot please."*
   - Assistant prompts for phone number.
6. Speak: *"My phone number is 9876543210."*
   - Assistant reads back: *"Just to confirm, I have your phone number as 9 8 7 6 5 4 3 2 1 0. Is that correct?"*
7. Speak: *"Yes, that is correct."*
   - Assistant confirms appointment with confirmation ID.
   - Note the in-phone confirmation card and the live dashboard table highlighting the new row in green!
8. Click **End Call** to hear the hangup chime.

---

## 📝 Short Pipeline Description (For Submission Form)

> *"The voice assistant pipeline is built using the Pipecat framework in Python. Inbound 16kHz audio from the browser WebSocket passes through Silero VAD for voice activity detection, into ElevenLabs STT for low-latency transcription. Google Gemini (gemini-2.0-flash) processes the conversational context and triggers registered function calls (check_doctor_availability, book_appointment, cancel_appointment) backed by SQLite. Before executing mutations, the prompt enforces a strict read-back confirmation of the caller's phone number. The generated response streams into ElevenLabs TTS, returning natural speech and real-time event frames back to a reactive React dashboard."*

---

## 📁 Project Structure

```
├── backend/
│   ├── clinic.db              # SQLite database (doctors, slots, appointments)
│   ├── database.py            # DB schema, queries, booking/cancellation logic
│   ├── main.py                # FastAPI server, REST routes & WebSocket endpoint
│   ├── mock_agent.py          # State engine & rule validation fallback
│   ├── pipeline.py            # Pipecat pipeline (Silero VAD + ElevenLabs + Gemini)
│   ├── serializer.py          # Custom WebSocket audio/event frame serializer
│   └── test_flow.py           # Automated E2E verification test
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AppointmentsTable.jsx  # Live appointments with highlight animation
│   │   │   ├── AudioWaveform.jsx      # Reactive audio visualizer canvas
│   │   │   ├── DoctorCard.jsx         # Doctor profile with open/booked slot pills
│   │   │   └── PhoneModal.jsx         # Smartphone call screen with transcript & controls
│   │   ├── utils/
│   │   │   └── audio.js               # Web Audio API ringtones & call sound effects
│   │   ├── App.jsx                    # Main dashboard layout
│   │   └── index.css                  # Tailwind styles & keyframes
│   ├── package.json
│   └── vite.config.js
├── .env.example               # Environment variables template
├── requirements.txt           # Python dependencies
├── run.py                     # Root single-command fullstack launcher
└── README.md                  # Documentation and submission guide
```
