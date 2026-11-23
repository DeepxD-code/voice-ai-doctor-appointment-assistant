"""
Database module for Voice AI Doctor Appointment Assistant.
Supports SQLite storage for doctors, available slots, and appointments.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "clinic.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        qualification TEXT NOT NULL,
        avatar TEXT NOT NULL,
        experience_years INTEGER NOT NULL,
        consultation_fee INTEGER NOT NULL,
        available_days TEXT NOT NULL,
        slots TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id TEXT UNIQUE NOT NULL,
        caller_phone TEXT NOT NULL,
        patient_name TEXT DEFAULT 'Caller',
        doctor_id INTEGER NOT NULL,
        doctor_name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        date TEXT NOT NULL,
        time_slot TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'CONFIRMED', -- CONFIRMED, CANCELLED
        created_at TEXT NOT NULL,
        FOREIGN KEY (doctor_id) REFERENCES doctors (id)
    )
    """)

    # Seed doctors if empty
    cursor.execute("SELECT COUNT(*) as count FROM doctors")
    count = cursor.fetchone()["count"]
    if count == 0:
        seed_doctors = [
            (
                "Dr. Sarah Jenkins",
                "Cardiology",
                "MD, FACC - Harvard Medical",
                "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=150&auto=format&fit=crop&q=80",
                14,
                120,
                json.dumps(["Monday", "Wednesday", "Friday"]),
                json.dumps(["09:00 AM", "10:30 AM", "02:00 PM", "03:30 PM", "04:30 PM"])
            ),
            (
                "Dr. Rajesh Sharma",
                "Dermatology",
                "MD, FAAD - Johns Hopkins",
                "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=150&auto=format&fit=crop&q=80",
                11,
                95,
                json.dumps(["Tuesday", "Thursday", "Saturday"]),
                json.dumps(["10:00 AM", "11:30 AM", "01:30 PM", "03:00 PM", "05:00 PM"])
            ),
            (
                "Dr. Elena Rostova",
                "Pediatrics",
                "MD - Stanford University",
                "https://images.unsplash.com/photo-1594824813571-638f0261f93f?w=150&auto=format&fit=crop&q=80",
                9,
                100,
                json.dumps(["Monday", "Tuesday", "Thursday", "Friday"]),
                json.dumps(["09:30 AM", "11:00 AM", "02:30 PM", "04:00 PM"])
            ),
            (
                "Dr. Marcus Chen",
                "General Medicine",
                "MD, MBBS - Oxford Medicine",
                "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=150&auto=format&fit=crop&q=80",
                16,
                80,
                json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
                json.dumps(["08:30 AM", "10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM", "05:00 PM"])
            ),
            (
                "Dr. Priya Patel",
                "Orthopedics",
                "MS, DNB - Mayo Clinic Fellow",
                "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=150&auto=format&fit=crop&q=80",
                12,
                130,
                json.dumps(["Monday", "Wednesday", "Thursday"]),
                json.dumps(["10:00 AM", "12:00 PM", "02:30 PM", "04:00 PM"])
            )
        ]
        cursor.executemany("""
        INSERT INTO doctors (name, specialty, qualification, avatar, experience_years, consultation_fee, available_days, slots)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_doctors)

        # Add initial sample appointments for demonstration
        today = datetime.now().strftime("%Y-%m-%d")
        seed_appointments = [
            ("APT-801", "9876543210", "Michael Scott", 1, "Dr. Sarah Jenkins", "Cardiology", today, "09:00 AM", "CONFIRMED", datetime.now().isoformat()),
            ("APT-802", "9123456780", "Pam Beesly", 2, "Dr. Rajesh Sharma", "Dermatology", today, "10:00 AM", "CONFIRMED", datetime.now().isoformat())
        ]
        cursor.executemany("""
        INSERT INTO appointments (appointment_id, caller_phone, patient_name, doctor_id, doctor_name, specialty, date, time_slot, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_appointments)

    conn.commit()
    conn.close()

def get_doctors(specialty: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if specialty:
        cursor.execute("SELECT * FROM doctors WHERE LOWER(specialty) LIKE LOWER(?)", (f"%{specialty}%",))
    else:
        cursor.execute("SELECT * FROM doctors")
    rows = cursor.fetchall()
    doctors = []
    for r in rows:
        d = dict(r)
        d["available_days"] = json.loads(d["available_days"])
        d["slots"] = json.loads(d["slots"])
        doctors.append(d)
    conn.close()
    return doctors

def check_doctor_availability(
    doctor_name: Optional[str] = None,
    date: Optional[str] = None,
    specialty: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns available slots for a doctor and/or specialty and date,
    filtering out any slots already booked.
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM doctors WHERE 1=1"
    params = []

    if doctor_name:
        # Match by partial doctor name (e.g. 'Jenkins', 'Sarah', 'Dr. Sarah Jenkins')
        clean_name = doctor_name.replace("Dr.", "").replace("Doctor", "").strip()
        query += " AND LOWER(name) LIKE LOWER(?)"
        params.append(f"%{clean_name}%")

    if specialty:
        query += " AND LOWER(specialty) LIKE LOWER(?)"
        params.append(f"%{specialty}%")

    cursor.execute(query, params)
    matched_doctors = cursor.fetchall()

    if not matched_doctors:
        conn.close()
        return {
            "status": "not_found",
            "message": f"No doctors found matching criteria (doctor: {doctor_name}, specialty: {specialty}).",
            "doctors": []
        }

    results = []
    for doc in matched_doctors:
        all_slots = json.loads(doc["slots"])
        # Query active appointments for this doctor on this date
        cursor.execute("""
            SELECT time_slot FROM appointments
            WHERE doctor_id = ? AND date = ? AND status = 'CONFIRMED'
        """, (doc["id"], date))
        booked_slots = {r["time_slot"] for r in cursor.fetchall()}

        available_slots = [slot for slot in all_slots if slot not in booked_slots]

        results.append({
            "doctor_id": doc["id"],
            "doctor_name": doc["name"],
            "specialty": doc["specialty"],
            "qualification": doc["qualification"],
            "date": date,
            "all_slots": all_slots,
            "available_slots": available_slots,
            "booked_slots": list(booked_slots)
        })

    conn.close()
    return {
        "status": "success",
        "date": date,
        "doctors": results
    }

def clean_phone(phone: str) -> str:
    """Normalize phone number to digits only"""
    if not phone:
        return ""
    digits = "".join(c for c in str(phone) if c.isdigit())
    # Keep last 10 digits if longer
    return digits[-10:] if len(digits) >= 10 else digits

def book_appointment(
    phone_number: str,
    doctor_name: str,
    date: str,
    time_slot: str,
    patient_name: str = "Caller"
) -> Dict[str, Any]:
    """
    Books a selected slot for the caller using the phone number they provided.
    """
    norm_phone = clean_phone(phone_number)
    if not norm_phone or len(norm_phone) < 7:
        return {
            "status": "error",
            "message": f"Invalid phone number provided: '{phone_number}'. A valid phone number is required."
        }

    conn = get_connection()
    cursor = conn.cursor()

    # Find doctor
    clean_name = doctor_name.replace("Dr.", "").replace("Doctor", "").strip()
    cursor.execute("SELECT * FROM doctors WHERE LOWER(name) LIKE LOWER(?)", (f"%{clean_name}%",))
    doctor = cursor.fetchone()

    if not doctor:
        conn.close()
        return {
            "status": "error",
            "message": f"Doctor '{doctor_name}' was not found. Please choose from our available doctors."
        }

    # Verify slot availability
    cursor.execute("""
        SELECT id FROM appointments
        WHERE doctor_id = ? AND date = ? AND time_slot = ? AND status = 'CONFIRMED'
    """, (doctor["id"], date, time_slot))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return {
            "status": "error",
            "message": f"Slot {time_slot} on {date} with {doctor['name']} is already booked. Please choose another time slot."
        }

    # Generate appointment ID
    import random
    apt_id = f"APT-{random.randint(1000, 9999)}"

    now_iso = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO appointments (appointment_id, caller_phone, patient_name, doctor_id, doctor_name, specialty, date, time_slot, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?)
    """, (apt_id, norm_phone, patient_name, doctor["id"], doctor["name"], doctor["specialty"], date, time_slot, now_iso))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "appointment_id": apt_id,
        "caller_phone": norm_phone,
        "doctor_name": doctor["name"],
        "specialty": doctor["specialty"],
        "date": date,
        "time_slot": time_slot,
        "message": f"Appointment {apt_id} successfully booked with {doctor['name']} on {date} at {time_slot} for phone number {norm_phone}."
    }

def cancel_appointment(
    phone_number: str,
    appointment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cancels the caller's existing appointment found using their phone number.
    """
    norm_phone = clean_phone(phone_number)
    if not norm_phone or len(norm_phone) < 7:
        return {
            "status": "error",
            "message": f"Invalid phone number provided: '{phone_number}'. A valid phone number is required to locate the appointment."
        }

    conn = get_connection()
    cursor = conn.cursor()

    if appointment_id:
        cursor.execute("""
            SELECT * FROM appointments
            WHERE caller_phone = ? AND appointment_id = ? AND status = 'CONFIRMED'
        """, (norm_phone, appointment_id))
    else:
        cursor.execute("""
            SELECT * FROM appointments
            WHERE caller_phone = ? AND status = 'CONFIRMED'
            ORDER BY id DESC LIMIT 1
        """, (norm_phone,))

    appt = cursor.fetchone()

    if not appt:
        conn.close()
        return {
            "status": "error",
            "message": f"No active appointment found for phone number {norm_phone}."
        }

    cursor.execute("""
        UPDATE appointments SET status = 'CANCELLED'
        WHERE id = ?
    """, (appt["id"],))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "appointment_id": appt["appointment_id"],
        "caller_phone": norm_phone,
        "doctor_name": appt["doctor_name"],
        "date": appt["date"],
        "time_slot": appt["time_slot"],
        "message": f"Appointment {appt['appointment_id']} with {appt['doctor_name']} on {appt['date']} at {appt['time_slot']} has been successfully cancelled."
    }

def get_all_appointments() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments ORDER BY id DESC")
    rows = cursor.fetchall()
    appts = [dict(r) for r in rows]
    conn.close()
    return appts

# Initialize DB on load
init_db()
