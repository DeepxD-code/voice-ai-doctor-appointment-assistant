"""
Pipecat Voice Pipeline for Doctor Appointment Assistant.
Configures:
- Transport: FastAPIWebsocketTransport with custom AudioAndControlSerializer
- VAD: VADProcessor with SileroVADAnalyzer
- STT: ElevenLabsSTTService
- LLM: GoogleLLMService (Gemini) with function calling tools
- TTS: ElevenLabsTTSService
"""

import os
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.adapters.llm.schemas.function_schema import FunctionSchema
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.google.llm import GoogleLLMService
from pipecat.services.elevenlabs.stt import ElevenLabsSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams

from backend.serializer import AudioAndControlSerializer
from backend.database import check_doctor_availability, book_appointment, cancel_appointment

SYSTEM_PROMPT = """You are the friendly, professional voice AI receptionist for Apex Health Medical Center.
You help callers:
1. Check doctor availability and view open appointment time slots.
2. Book an appointment with a chosen doctor, date, and slot.
3. Cancel an existing appointment.

CRITICAL ASSIGNMENT RULES (YOU MUST ALWAYS FOLLOW):
1. Identification: The caller is identified ONLY by the phone number they say out loud. No login, no OTP, no caller-ID.
2. Read-back Confirmation: Whenever a caller wants to book or cancel an appointment, you MUST read the phone number back to them to confirm before executing the action!
   Example: "Just to confirm, I have your phone number as 9-8-7-6-5-4-3-2-1-0. Is that correct?"
   Only after they say yes / confirm do you call the tool to book or cancel.
3. Natural Voice Conversation: Keep spoken responses concise, conversational, and warm (1-2 sentences). Do not use bullet points or markdown in spoken output.
4. Available Doctors & Specialties:
   - Dr. Sarah Jenkins (Cardiology)
   - Dr. Rajesh Sharma (Dermatology)
   - Dr. Elena Rostova (Pediatrics)
   - Dr. Marcus Chen (General Medicine)
   - Dr. Priya Patel (Orthopedics)
5. You can handle checking availability, booking, and cancellation all in one continuous call.
"""

def create_appointment_tools(on_tool_event=None):
    """Create the function calling schemas and handlers for Pipecat LLM"""

    async def handle_check_availability(params: FunctionCallParams):
        args = params.arguments
        doctor_name = args.get("doctor_name")
        date = args.get("date")
        specialty = args.get("specialty")

        logger.info(f"Tool check_doctor_availability called with: {args}")
        result = check_doctor_availability(
            doctor_name=doctor_name,
            date=date,
            specialty=specialty
        )

        if on_tool_event:
            await on_tool_event("check_doctor_availability", args, result)

        await params.result_callback(result)

    async def handle_book_appointment(params: FunctionCallParams):
        args = params.arguments
        phone = args.get("phone_number")
        doctor = args.get("doctor_name")
        date = args.get("date")
        slot = args.get("time_slot")
        patient = args.get("patient_name", "Caller")

        logger.info(f"Tool book_appointment called with: {args}")
        result = book_appointment(
            phone_number=phone,
            doctor_name=doctor,
            date=date,
            time_slot=slot,
            patient_name=patient
        )

        if on_tool_event:
            await on_tool_event("book_appointment", args, result)

        await params.result_callback(result)

    async def handle_cancel_appointment(params: FunctionCallParams):
        args = params.arguments
        phone = args.get("phone_number")
        apt_id = args.get("appointment_id")

        logger.info(f"Tool cancel_appointment called with: {args}")
        result = cancel_appointment(
            phone_number=phone,
            appointment_id=apt_id
        )

        if on_tool_event:
            await on_tool_event("cancel_appointment", args, result)

        await params.result_callback(result)

    check_avail_schema = FunctionSchema(
        name="check_doctor_availability",
        description="Returns available slots for a doctor and/or date and specialty so the agent can offer them to the caller.",
        properties={
            "doctor_name": {
                "type": "string",
                "description": "Doctor's name (e.g. 'Dr. Sarah Jenkins' or 'Jenkins')"
            },
            "date": {
                "type": "string",
                "description": "Target date in YYYY-MM-DD format. If omitted, today is used."
            },
            "specialty": {
                "type": "string",
                "description": "Medical specialty (Cardiology, Dermatology, Pediatrics, General Medicine, Orthopedics)"
            }
        },
        required=[],
        handler=handle_check_availability
    )

    book_appt_schema = FunctionSchema(
        name="book_appointment",
        description="Books a selected slot for the caller, using the phone number the caller told the agent. Must confirm phone number before calling.",
        properties={
            "phone_number": {
                "type": "string",
                "description": "The caller's 10-digit phone number, confirmed by reading back to the caller."
            },
            "doctor_name": {
                "type": "string",
                "description": "Full or surname of the doctor to book with."
            },
            "date": {
                "type": "string",
                "description": "Appointment date in YYYY-MM-DD format."
            },
            "time_slot": {
                "type": "string",
                "description": "Selected time slot, e.g. '10:30 AM' or '02:00 PM'."
            },
            "patient_name": {
                "type": "string",
                "description": "Name of the caller if provided, else 'Caller'."
            }
        },
        required=["phone_number", "doctor_name", "date", "time_slot"],
        handler=handle_book_appointment
    )

    cancel_appt_schema = FunctionSchema(
        name="cancel_appointment",
        description="Cancels the caller's existing appointment, found using the phone number the caller told the agent. Must confirm phone number before calling.",
        properties={
            "phone_number": {
                "type": "string",
                "description": "The caller's confirmed phone number used to locate their appointment."
            },
            "appointment_id": {
                "type": "string",
                "description": "Optional specific appointment ID (e.g. APT-801) if caller specified it."
            }
        },
        required=["phone_number"],
        handler=handle_cancel_appointment
    )

    return [check_avail_schema, book_appt_schema, cancel_appt_schema]

async def build_pipecat_pipeline(
    websocket,
    aiohttp_session: aiohttp.ClientSession,
    on_tool_event=None
):
    """
    Constructs and returns the complete Pipecat voice pipeline task & runner.
    """
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    eleven_key = os.getenv("ELEVENLABS_API_KEY")

    # Validate that keys are real and not default template placeholders
    if (not gemini_key or "your_" in gemini_key or
        not eleven_key or "your_" in eleven_key):
        logger.info("Using Interactive Voice Assistant Engine (cloud API keys not yet configured or template values).")
        return None

    # 1. Custom Serializer for WebSocket
    serializer = AudioAndControlSerializer(sample_rate=16000)

    # 2. FastAPI WebSocket Transport
    transport_params = FastAPIWebsocketParams(
        serializer=serializer,
        add_wav_header=False,
    )
    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=transport_params,
    )

    # 3. Silero VAD (Bonus backend requirement: wrapped in VADProcessor)
    vad_analyzer = SileroVADAnalyzer(sample_rate=16000)
    vad_processor = VADProcessor(vad_analyzer=vad_analyzer)

    # 4. ElevenLabs STT (Speech-to-text)
    stt = ElevenLabsSTTService(
        api_key=eleven_key,
        aiohttp_session=aiohttp_session,
    )

    # 5. Tools & LLM Context
    tools = create_appointment_tools(on_tool_event=on_tool_event)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    context = LLMContext(
        messages=messages,
        tools=tools,
    )
    context_aggregator = LLMContextAggregatorPair(context)

    # 6. Google Gemini LLM Service
    llm = GoogleLLMService(
        api_key=gemini_key,
        settings=GoogleLLMService.Settings(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            system_instruction=SYSTEM_PROMPT,
        ),
        tools=tools,
    )

    # 7. ElevenLabs TTS (Text-to-speech)
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM") # Rachel
    tts = ElevenLabsTTSService(
        api_key=eleven_key,
        voice_id=voice_id,
        model="eleven_flash_v2_5",
        sample_rate=16000,
    )

    # 8. Pipecat Pipeline
    pipeline = Pipeline([
        transport.input(),
        vad_processor,
        stt,
        context_aggregator.user(),
        llm,
        tts,
        transport.output(),
        context_aggregator.assistant(),
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            audio_in_sample_rate=16000,
            audio_out_sample_rate=16000,
        )
    )

    runner = PipelineRunner()

    return {
        "task": task,
        "runner": runner,
        "transport": transport,
        "context": context,
    }
