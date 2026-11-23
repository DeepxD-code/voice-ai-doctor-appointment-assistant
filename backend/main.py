"""
FastAPI Server for Voice AI Doctor Appointment Assistant.
Hosts REST API for dashboard and WebSocket for real-time voice call.
"""

import os
import json
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

from backend.database import (
    init_db,
    get_doctors,
    check_doctor_availability,
    book_appointment,
    cancel_appointment,
    get_all_appointments,
)
from backend.mock_agent import ConversationEngine
from backend.pipeline import build_pipecat_pipeline

app = FastAPI(title="Voice AI Doctor Appointment Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active connected dashboard WebSockets for real-time sync
connected_clients: List[WebSocket] = []

async def broadcast_event(event_type: str, data: Dict[str, Any]):
    """Broadcast state changes to all connected dashboard websockets"""
    message = json.dumps({"type": event_type, "data": data})
    disconnected = []
    for ws in connected_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in connected_clients:
            connected_clients.remove(ws)

# REST Endpoints
@app.get("/api/config")
async def get_config():
    gemini_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    eleven_key = bool(os.getenv("ELEVENLABS_API_KEY"))
    return {
        "gemini_configured": gemini_key,
        "elevenlabs_configured": eleven_key,
        "mode": "pipecat_cloud" if (gemini_key and eleven_key) else "local_interactive",
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    }

@app.get("/api/doctors")
async def api_get_doctors(specialty: Optional[str] = None):
    return get_doctors(specialty=specialty)

@app.get("/api/availability")
async def api_check_availability(
    doctor_name: Optional[str] = None,
    date: Optional[str] = None,
    specialty: Optional[str] = None
):
    return check_doctor_availability(
        doctor_name=doctor_name,
        date=date,
        specialty=specialty
    )

@app.get("/api/appointments")
async def api_get_appointments():
    return get_all_appointments()

class BookingRequest(BaseModel):
    phone_number: str
    doctor_name: str
    date: str
    time_slot: str
    patient_name: Optional[str] = "Caller"

@app.post("/api/appointments/book")
async def api_book_appointment(req: BookingRequest):
    result = book_appointment(
        phone_number=req.phone_number,
        doctor_name=req.doctor_name,
        date=req.date,
        time_slot=req.time_slot,
        patient_name=req.patient_name
    )
    if result.get("status") == "success":
        await broadcast_event("appointment_updated", {
            "action": "book",
            "appointment": result
        })
    return result

class CancelRequest(BaseModel):
    phone_number: str
    appointment_id: Optional[str] = None

@app.post("/api/appointments/cancel")
async def api_cancel_appointment(req: CancelRequest):
    result = cancel_appointment(
        phone_number=req.phone_number,
        appointment_id=req.appointment_id
    )
    if result.get("status") == "success":
        await broadcast_event("appointment_updated", {
            "action": "cancel",
            "appointment": result
        })
    return result

@app.post("/api/reset")
async def api_reset():
    db_file = os.path.join(os.path.dirname(__file__), "clinic.db")
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
    init_db()
    await broadcast_event("data_reset", {})
    return {"status": "success", "message": "Database reset to initial state."}

# WebSocket Endpoint for Voice Agent Call
@app.websocket("/ws/call")
async def websocket_call_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    logger.info("New voice call WebSocket connected.")

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    eleven_key = os.getenv("ELEVENLABS_API_KEY")

    async def on_tool_event(function_name: str, args: dict, result: dict):
        logger.info(f"Tool executed: {function_name} -> {result.get('status')}")
        # Broadcast tool result to frontend dashboard
        await broadcast_event("tool_executed", {
            "function_name": function_name,
            "args": args,
            "result": result
        })
        if function_name in ("book_appointment", "cancel_appointment"):
            await broadcast_event("appointment_updated", {
                "action": "book" if function_name == "book_appointment" else "cancel",
                "appointment": result
            })

    # Check if full Pipecat pipeline with cloud API keys can run
    is_cloud_keys_configured = (
        gemini_key and "your_" not in gemini_key and
        eleven_key and "your_" not in eleven_key
    )

    if is_cloud_keys_configured:
        logger.info("Running full Pipecat pipeline (Gemini + ElevenLabs STT/TTS + Silero VAD)")
        try:
            async with aiohttp.ClientSession() as aiohttp_session:
                pipeline_bundle = await build_pipecat_pipeline(
                    websocket=websocket,
                    aiohttp_session=aiohttp_session,
                    on_tool_event=on_tool_event
                )
                if pipeline_bundle:
                    await pipeline_bundle["runner"].run(pipeline_bundle["task"])
                    return
        except Exception as e:
            logger.error(f"Pipecat pipeline error, transitioning to interactive assistant: {e}")

    # Fallback / Interactive Local Voice Engine
    logger.info("Operating in Interactive Voice Assistant engine mode.")
    engine = ConversationEngine(on_tool_event=on_tool_event)

    # Send initial greeting
    greeting = "Hello! Thank you for calling Apex Health Medical Center. I can check doctor availability, book appointments, or cancel existing ones. How can I assist you today?"
    await websocket.send_text(json.dumps({
        "type": "transcript",
        "role": "assistant",
        "text": greeting,
        "is_final": True
    }))

    try:
        while True:
            raw_msg = await websocket.receive()
            if "text" in raw_msg:
                try:
                    payload = json.loads(raw_msg["text"])
                    msg_type = payload.get("type")

                    if msg_type in ("user_speech", "user_text"):
                        user_text = payload.get("text", "").strip()
                        if not user_text:
                            continue

                        # Echo user transcript
                        await websocket.send_text(json.dumps({
                            "type": "transcript",
                            "role": "user",
                            "text": user_text,
                            "is_final": True
                        }))

                        # Process with engine
                        processed = await engine.process_user_utterance(user_text)

                        # Send assistant reply
                        await websocket.send_text(json.dumps({
                            "type": "transcript",
                            "role": "assistant",
                            "text": processed["reply"],
                            "is_final": True
                        }))

                        # If tool action was taken, send event
                        if processed.get("tool_action"):
                            await websocket.send_text(json.dumps({
                                "type": "tool_call_result",
                                "function_name": processed["tool_action"],
                                "result": processed.get("result", {})
                            }))

                    elif msg_type == "end_call":
                        await websocket.send_text(json.dumps({
                            "type": "call_ended",
                            "message": "Call completed."
                        }))
                        break

                except json.JSONDecodeError:
                    pass
            elif "bytes" in raw_msg:
                # Binary audio incoming (e.g. PCM chunk)
                # In interactive engine, audio frames can drive audio activity indicators
                pass

    except WebSocketDisconnect:
        logger.info("Voice call WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

# Mount frontend build if it exists
dist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
