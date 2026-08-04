import uuid
from typing import Any, Dict, List
from utils.helpers import load_json_file, save_json_file

class AppointmentTool:
    """
    Tool for managing appointment bookings, cancellations, and rescheduling.
    """
    def __init__(self, json_path: str = "data/appointments.json"):
        self.json_path = json_path

    def book_appointment(
        self,
        patient_id: str,
        doctor_id: str,
        date: str,
        time_slot: str,
        reason: str = "General Consultation"
    ) -> Dict[str, Any]:
        """
        Books a new appointment entry in appointments.json.
        """
        appointments = load_json_file(self.json_path, default=[])
        
        # Load doctor and patient info for enriched booking details
        doctors = load_json_file("data/doctors.json", default=[])
        patients = load_json_file("data/patients.json", default=[])
        
        doctor_name = next((d.get("full_name") for d in doctors if d.get("doctor_id") == doctor_id), "Doctor")
        patient_name = next((p.get("full_name") for p in patients if p.get("patient_id") == patient_id), "Patient")

        new_apt_id = f"APT{len(appointments) + 1001}"
        new_appointment = {
            "appointment_id": new_apt_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "appointment_date": date,
            "time_slot": time_slot,
            "status": "Scheduled",
            "reason_for_visit": reason
        }
        
        appointments.append(new_appointment)
        save_json_file(self.json_path, appointments)
        return {
            "status": "Success",
            "message": f"Appointment successfully booked for {patient_name} with {doctor_name} on {date} at {time_slot}.",
            "appointment": new_appointment
        }

    def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """
        Cancels an existing appointment.
        """
        appointments = load_json_file(self.json_path, default=[])
        for apt in appointments:
            if apt.get("appointment_id") == appointment_id:
                apt["status"] = "Cancelled"
                save_json_file(self.json_path, appointments)
                return {
                    "status": "Success",
                    "message": f"Appointment {appointment_id} has been cancelled successfully.",
                    "appointment": apt
                }
        return {"status": "Error", "message": f"Appointment {appointment_id} not found."}

    def reschedule_appointment(self, appointment_id: str, new_date: str, new_time_slot: str) -> Dict[str, Any]:
        """
        Reschedules an existing appointment to a new date and time slot.
        """
        appointments = load_json_file(self.json_path, default=[])
        for apt in appointments:
            if apt.get("appointment_id") == appointment_id:
                apt["appointment_date"] = new_date
                apt["time_slot"] = new_time_slot
                apt["status"] = "Rescheduled"
                save_json_file(self.json_path, appointments)
                return {
                    "status": "Success",
                    "message": f"Appointment {appointment_id} successfully rescheduled to {new_date} at {new_time_slot}.",
                    "appointment": apt
                }
        return {"status": "Error", "message": f"Appointment {appointment_id} not found."}
