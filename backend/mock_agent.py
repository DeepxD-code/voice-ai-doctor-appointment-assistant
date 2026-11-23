"""
Conversational State Engine for Doctor Appointment Assistant.
Handles natural dialog, phone number verification rule, tool executions,
and dashboard synchronization. Used as fallback when cloud API keys are absent,
or as direct test agent.
"""

import re
from datetime import datetime
from typing import Dict, Any, Tuple
from loguru import logger
from backend.database import check_doctor_availability, book_appointment, cancel_appointment

class ConversationEngine:
    def __init__(self, on_tool_event=None):
        self.on_tool_event = on_tool_event
        self.reset()

    def reset(self):
        self.pending_action = None  # "book" or "cancel"
        self.pending_phone = None
        self.pending_doctor = "Dr. Sarah Jenkins"
        self.pending_date = datetime.now().strftime("%Y-%m-%d")
        self.pending_slot = "10:30 AM"
        self.phone_confirmed = False
        self.last_asked = None

    def extract_phone(self, text: str) -> str:
        # Extract digits sequence from text
        digits = re.findall(r'\d+', text)
        joined = "".join(digits)
        if len(joined) >= 7:
            return joined[-10:] if len(joined) >= 10 else joined
        return ""

    def format_phone_digits(self, phone: str) -> str:
        return " ".join(list(phone))

    async def process_user_utterance(self, text: str) -> Dict[str, Any]:
        """
        Process speech-to-text text from user, execute appropriate tools,
        and return AI response text and tool actions.
        """
        clean = text.lower().strip()
        logger.info(f"Processing utterance: '{text}' (pending_action={self.pending_action}, phone={self.pending_phone})")

        # 1. Check for Phone Number Confirmation ("yes", "correct", "that is right")
        if self.pending_action and self.pending_phone and not self.phone_confirmed:
            if any(w in clean for w in ["yes", "yeah", "correct", "right", "sure", "yep", "proceed", "confirm"]):
                self.phone_confirmed = True
                if self.pending_action == "book":
                    result = book_appointment(
                        phone_number=self.pending_phone,
                        doctor_name=self.pending_doctor,
                        date=self.pending_date,
                        time_slot=self.pending_slot,
                        patient_name="Caller"
                    )
                    if self.on_tool_event:
                        await self.on_tool_event("book_appointment", {
                            "phone_number": self.pending_phone,
                            "doctor_name": self.pending_doctor,
                            "date": self.pending_date,
                            "time_slot": self.pending_slot
                        }, result)

                    action_taken = "book_appointment"
                    if result["status"] == "success":
                        reply = f"Thank you! Your appointment with {result['doctor_name']} has been confirmed for {result['date']} at {result['time_slot']}. Your appointment ID is {result['appointment_id']}. Is there anything else I can help you with?"
                    else:
                        reply = f"I'm sorry, {result['message']}. Would you like to select another time slot?"

                    self.pending_action = None
                    self.pending_phone = None
                    self.phone_confirmed = False
                    return {"reply": reply, "tool_action": action_taken, "result": result}

                elif self.pending_action == "cancel":
                    result = cancel_appointment(phone_number=self.pending_phone)
                    if self.on_tool_event:
                        await self.on_tool_event("cancel_appointment", {"phone_number": self.pending_phone}, result)

                    action_taken = "cancel_appointment"
                    if result["status"] == "success":
                        reply = f"Your appointment {result['appointment_id']} with {result['doctor_name']} on {result['date']} at {result['time_slot']} has been successfully cancelled. Can I help you with anything else?"
                    else:
                        reply = f"I checked our records, but {result['message']} Please let me know if you would like me to check a different number."

                    self.pending_action = None
                    self.pending_phone = None
                    self.phone_confirmed = False
                    return {"reply": reply, "tool_action": action_taken, "result": result}

            elif any(w in clean for w in ["no", "wrong", "incorrect", "change"]):
                self.pending_phone = None
                return {
                    "reply": "I apologize. Could you please repeat your 10-digit phone number?",
                    "tool_action": None
                }

        # 2. Extract Phone Number if mentioned in utterance
        extracted_phone = self.extract_phone(clean)
        if extracted_phone:
            self.pending_phone = extracted_phone
            # Rule: MUST read the phone number back to caller to confirm before booking or cancelling
            phone_spoken = self.format_phone_digits(self.pending_phone)
            action_name = "booking" if self.pending_action == "book" else "cancelling" if self.pending_action == "cancel" else "your request"
            return {
                "reply": f"Just to confirm, I have your phone number as {phone_spoken}. Is that correct?",
                "tool_action": "phone_confirmation_requested",
                "phone": self.pending_phone
            }

        # 3. Check for Cancellation Intent
        if any(w in clean for w in ["cancel", "cancellation", "drop"]):
            self.pending_action = "cancel"
            if not self.pending_phone:
                return {
                    "reply": "I can certainly help you cancel your appointment. May I please have the phone number you used when booking?",
                    "tool_action": None
                }
            else:
                phone_spoken = self.format_phone_digits(self.pending_phone)
                return {
                    "reply": f"Just to confirm, I have your phone number as {phone_spoken}. Shall I proceed with cancelling your appointment?",
                    "tool_action": "phone_confirmation_requested"
                }

        # 4. Check for Booking Intent & Slots
        if any(w in clean for w in ["book", "schedule", "reserve", "take", "slot"]):
            self.pending_action = "book"

            # Check if doctor name mentioned
            if "jenkins" in clean or "sarah" in clean:
                self.pending_doctor = "Dr. Sarah Jenkins"
            elif "sharma" in clean or "rajesh" in clean:
                self.pending_doctor = "Dr. Rajesh Sharma"
            elif "rostova" in clean or "elena" in clean:
                self.pending_doctor = "Dr. Elena Rostova"
            elif "chen" in clean or "marcus" in clean:
                self.pending_doctor = "Dr. Marcus Chen"
            elif "patel" in clean or "priya" in clean:
                self.pending_doctor = "Dr. Priya Patel"

            # Check if time mentioned
            time_matches = re.findall(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm))', clean)
            if time_matches:
                t = time_matches[0].upper()
                if ":" not in t:
                    t = t.replace("AM", ":00 AM").replace("PM", ":00 PM")
                self.pending_slot = t

            if not self.pending_phone:
                return {
                    "reply": f"I'd be glad to book {self.pending_slot} with {self.pending_doctor}. May I please have your phone number to reserve the slot?",
                    "tool_action": None
                }
            else:
                phone_spoken = self.format_phone_digits(self.pending_phone)
                return {
                    "reply": f"Just to confirm, I have your phone number as {phone_spoken}. Is that correct?",
                    "tool_action": "phone_confirmation_requested"
                }

        # 5. Check for Availability or Doctor Inquiry
        if any(w in clean for w in ["available", "availability", "slot", "slots", "doctor", "doctors", "cardiology", "dermatology", "pediatrics"]):
            doc_query = None
            spec_query = None
            if "jenkins" in clean or "sarah" in clean:
                doc_query = "Jenkins"
            elif "sharma" in clean or "rajesh" in clean:
                doc_query = "Sharma"
            elif "rostova" in clean or "elena" in clean:
                doc_query = "Rostova"
            elif "chen" in clean or "marcus" in clean:
                doc_query = "Chen"
            elif "patel" in clean or "priya" in clean:
                doc_query = "Patel"
            elif "cardio" in clean:
                spec_query = "Cardiology"
            elif "derma" in clean:
                spec_query = "Dermatology"
            elif "pediatric" in clean:
                spec_query = "Pediatrics"

            avail = check_doctor_availability(doctor_name=doc_query, specialty=spec_query)
            if self.on_tool_event:
                await self.on_tool_event("check_doctor_availability", {
                    "doctor_name": doc_query,
                    "specialty": spec_query
                }, avail)

            if avail["status"] == "success" and avail["doctors"]:
                doc = avail["doctors"][0]
                self.pending_doctor = doc["doctor_name"]
                slots = ", ".join(doc["available_slots"][:3])
                reply = f"{doc['doctor_name']} ({doc['specialty']}) has available slots: {slots}. Which one would suit you best?"
                return {
                    "reply": reply,
                    "tool_action": "check_doctor_availability",
                    "result": avail
                }
            else:
                return {
                    "reply": "We have Dr. Sarah Jenkins in Cardiology, Dr. Rajesh Sharma in Dermatology, and Dr. Marcus Chen in General Medicine available today. Who would you like to see?",
                    "tool_action": "check_doctor_availability"
                }

        # 6. Default / Greetings
        if any(w in clean for w in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return {
                "reply": "Hello! Welcome to Apex Health Medical Center. I can help you check doctor availability, book an appointment, or cancel an existing booking. How can I help you today?",
                "tool_action": None
            }

        return {
            "reply": "I can help you check doctor availability, book an appointment, or cancel one. Would you like to check available slots for Dr. Sarah Jenkins or another specialist?",
            "tool_action": None
        }
