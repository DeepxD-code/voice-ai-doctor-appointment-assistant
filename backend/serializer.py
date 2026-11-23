"""
Custom FrameSerializer for bidirectional Web Audio streaming & event synchronization
between the browser and Pipecat pipeline.
"""

import json
import base64
from typing import Optional, Union
from loguru import logger
from pydantic import BaseModel

from pipecat.frames.frames import (
    Frame,
    InputAudioRawFrame,
    OutputAudioRawFrame,
    TTSAudioRawFrame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
    TextFrame,
    TTSTextFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    FunctionCallInProgressFrame,
    FunctionCallResultFrame,
)
from pipecat.serializers.base_serializer import FrameSerializer

class AudioAndControlSerializer(FrameSerializer):
    """
    Serializes frames to/from the frontend WebSocket.
    Audio is transferred as binary PCM (or base64 JSON), while control
    and transcript messages are JSON strings.
    """

    def __init__(self, sample_rate: int = 16000):
        params = FrameSerializer.InputParams(
            audio_in_sample_rate=sample_rate,
            audio_out_sample_rate=sample_rate,
        )
        super().__init__(params=params)
        self.sample_rate = sample_rate

    async def serialize(self, frame: Frame) -> Optional[Union[str, bytes]]:
        # Handle Output Audio frames (from ElevenLabs TTS)
        if isinstance(frame, (OutputAudioRawFrame, TTSAudioRawFrame)):
            return frame.audio

        # Handle User Transcription (from ElevenLabs STT)
        elif isinstance(frame, TranscriptionFrame):
            return json.dumps({
                "type": "transcript",
                "role": "user",
                "text": frame.text,
                "is_final": True,
            })

        elif isinstance(frame, InterimTranscriptionFrame):
            return json.dumps({
                "type": "transcript",
                "role": "user",
                "text": frame.text,
                "is_final": False,
            })

        # Handle Bot / Assistant Text
        elif isinstance(frame, (TTSTextFrame, TextFrame)):
            if frame.text and frame.text.strip():
                return json.dumps({
                    "type": "transcript",
                    "role": "assistant",
                    "text": frame.text,
                })

        # Handle Speech Start / Stop events (for audio visualizer / speaking indicators)
        elif isinstance(frame, BotStartedSpeakingFrame):
            return json.dumps({"type": "bot_speaking", "speaking": True})

        elif isinstance(frame, BotStoppedSpeakingFrame):
            return json.dumps({"type": "bot_speaking", "speaking": False})

        elif isinstance(frame, UserStartedSpeakingFrame):
            return json.dumps({"type": "user_speaking", "speaking": True})

        elif isinstance(frame, UserStoppedSpeakingFrame):
            return json.dumps({"type": "user_speaking", "speaking": False})

        # Handle Tool Calls (for real-time dashboard updates)
        elif isinstance(frame, FunctionCallInProgressFrame):
            return json.dumps({
                "type": "tool_call_start",
                "function_name": frame.function_name,
                "arguments": frame.arguments,
            })

        elif isinstance(frame, FunctionCallResultFrame):
            return json.dumps({
                "type": "tool_call_result",
                "function_name": frame.function_name,
                "arguments": frame.arguments,
                "result": frame.result,
            })

        return None

    async def deserialize(self, data: Union[str, bytes]) -> Optional[Frame]:
        # If binary audio data arrives from browser microphone
        if isinstance(data, bytes):
            return InputAudioRawFrame(
                audio=data,
                sample_rate=self.sample_rate,
                num_channels=1,
            )

        # If text/JSON arrives from browser
        if isinstance(data, str):
            try:
                payload = json.loads(data)
                msg_type = payload.get("type")

                if msg_type == "audio_base64":
                    raw_audio = base64.b64decode(payload.get("data", ""))
                    return InputAudioRawFrame(
                        audio=raw_audio,
                        sample_rate=self.sample_rate,
                        num_channels=1,
                    )
                elif msg_type == "user_text":
                    # Support text prompt injection (e.g. typing directly or WebSpeech fallback)
                    return TranscriptionFrame(
                        text=payload.get("text", ""),
                        user_id="caller",
                        timestamp=payload.get("timestamp", ""),
                    )
            except Exception as e:
                logger.warning(f"Error deserializing message: {e}")

        return None
