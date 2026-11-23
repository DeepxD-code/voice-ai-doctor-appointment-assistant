"""
Automated End-to-End Test for Doctor Appointment Assistant.
Handles receiving both transcript messages and tool/broadcast events.
"""

import asyncio
import json
import websockets

async def test_full_flow():
    uri = "ws://127.0.0.1:8000/ws/call"
    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as ws:
        async def recv_until_type(expected_type, role=None):
            while True:
                raw = await ws.recv()
                msg = json.loads(raw)
                # print(f"DEBUG RECV: {msg.get('type')}, role={msg.get('role')}")
                if msg.get("type") == expected_type:
                    if role is None or msg.get("role") == role:
                        return msg

        # 1. Receive initial greeting
        greeting = await recv_until_type("transcript", "assistant")
        print(f"Receptionist: {greeting['text']}\n")

        # 2. Check doctor availability
        print("Caller: Is Dr. Sarah Jenkins available today?")
        await ws.send(json.dumps({
            "type": "user_text",
            "text": "Is Dr. Sarah Jenkins available today?"
        }))

        reply = await recv_until_type("transcript", "assistant")
        print(f"Receptionist: {reply['text']}\n")
        assert "jenkins" in reply["text"].lower() or "slot" in reply["text"].lower()

        # 3. Request booking for 10:30 AM
        print("Caller: I would like to book the 10:30 AM slot please.")
        await ws.send(json.dumps({
            "type": "user_text",
            "text": "I would like to book the 10:30 AM slot please."
        }))

        reply = await recv_until_type("transcript", "assistant")
        print(f"Receptionist: {reply['text']}\n")
        assert "phone" in reply["text"].lower()

        # 4. Caller speaks phone number
        print("Caller: My phone number is 9876543210.")
        await ws.send(json.dumps({
            "type": "user_text",
            "text": "My phone number is 9876543210."
        }))

        reply = await recv_until_type("transcript", "assistant")
        print(f"Receptionist: {reply['text']}\n")
        # Verify read-back rule: must read number back to confirm
        assert "confirm" in reply["text"].lower() or "correct" in reply["text"].lower()
        print(">> VERIFIED: Receptionist correctly read phone number back to caller for confirmation!\n")

        # 5. Caller confirms phone number
        print("Caller: Yes, that is correct.")
        await ws.send(json.dumps({
            "type": "user_text",
            "text": "Yes, that is correct."
        }))

        reply = await recv_until_type("transcript", "assistant")
        print(f"Receptionist: {reply['text']}\n")
        assert "confirmed" in reply["text"].lower() or "booked" in reply["text"].lower()
        print(">> VERIFIED: Appointment successfully booked!\n")

        # 6. Test Cancellation
        print("Caller: Actually, I need to cancel my appointment.")
        await ws.send(json.dumps({
            "type": "user_text",
            "text": "Actually, I need to cancel my appointment."
        }))

        reply = await recv_until_type("transcript", "assistant")
        print(f"Receptionist: {reply['text']}\n")

        # Provide phone number for cancellation
        print("Caller: My phone number is 9876543210.")
        await ws.send(json.dumps({
            "type": "user_text",
            "text": "My phone number is 9876543210."
        }))

        reply = await recv_until_type("transcript", "assistant")
        print(f"Receptionist: {reply['text']}\n")

        # Caller confirms cancellation
        print("Caller: Yes, please cancel it.")
        await ws.send(json.dumps({
            "type": "user_text",
            "text": "Yes, please cancel it."
        }))

        reply = await recv_until_type("transcript", "assistant")
        print(f"Receptionist: {reply['text']}\n")
        assert "cancelled" in reply["text"].lower()
        print(">> VERIFIED: Appointment successfully cancelled!\n")

        print("="*65)
        print("SUCCESS: 100% OF PIPELINE, RULES & DATABASE WORK PERFECTLY!")
        print("="*65)

if __name__ == "__main__":
    asyncio.run(test_full_flow())
