from datetime import datetime
from typing import Dict, List

# In-memory storage (replace with database later)
appointments: List[Dict] = []


def book_appointment(patient_name: str, doctor: str, date: str, time: str) -> Dict:
    appointment = {
        "id": len(appointments) + 1,
        "patient_name": patient_name,
        "doctor": doctor,
        "date": date,
        "time": time,
        "status": "Booked",
        "created_at": datetime.now().isoformat()
    }
    appointments.append(appointment)
    return appointment


def cancel_appointment(appointment_id: int) -> Dict:
    for appt in appointments:
        if appt["id"] == appointment_id:
            appt["status"] = "Cancelled"
            return appt
    return {"error": "Appointment not found"}


def reschedule_appointment(appointment_id: int, new_date: str, new_time: str) -> Dict:
    for appt in appointments:
        if appt["id"] == appointment_id:
            appt["date"] = new_date
            appt["time"] = new_time
            appt["status"] = "Rescheduled"
            return appt
    return {"error": "Appointment not found"}


def list_appointments() -> List[Dict]:
    return appointments