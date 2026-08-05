import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from utils.helpers import load_json_file, save_json_file

DATA_FILE = "data/appointments.json"


class AppointmentTool:
    """
    Tool for reading and persisting appointments to data/appointments.json.
    Supports booking, cancelling, rescheduling, and listing appointments.
    """

    def _load_appointments(self) -> List[Dict]:
        return load_json_file(DATA_FILE, default=[])

    def _save_appointments(self, appointments: List[Dict]) -> None:
        save_json_file(DATA_FILE, appointments)

    def _generate_appointment_id(self, appointments: List[Dict]) -> str:
        existing_ids = [
            int(a["appointment_id"].replace("APT", ""))
            for a in appointments
            if a.get("appointment_id", "").startswith("APT")
        ]
        next_id = max(existing_ids, default=1000) + 1
        return f"APT{next_id}"

    def _check_conflicts(
        self,
        appointments: list,
        date: str,
        time_slot: str,
        patient_id: str = "",
        doctor_id: str = "",
        exclude_id: str = "",
    ) -> dict | None:
        """
        Returns an error dict if a scheduling conflict exists, else None.
        Checks active (Scheduled / Rescheduled) appointments only.
        """
        active_statuses = {"Scheduled", "Rescheduled"}
        for appt in appointments:
            if appt.get("appointment_id") == exclude_id:
                continue
            if appt.get("status") not in active_statuses:
                continue
            same_slot = (
                appt.get("appointment_date") == date
                and appt.get("time_slot", "").strip().upper() == time_slot.strip().upper()
            )
            if not same_slot:
                continue
            # Patient double-booking
            if patient_id and appt.get("patient_id") == patient_id:
                return {
                    "status": "Error",
                    "message": (
                        f"⚠️ **Double-booking prevented.** Patient already has appointment "
                        f"`{appt.get('appointment_id')}` on **{date}** at **{time_slot}**. "
                        "Please choose a different date or time slot."
                    ),
                }
            # Doctor double-booking
            if doctor_id and appt.get("doctor_id") == doctor_id:
                return {
                    "status": "Error",
                    "message": (
                        f"⚠️ **Slot unavailable.** Dr. {appt.get('doctor_name', doctor_id)} "
                        f"already has a booking on **{date}** at **{time_slot}**. "
                        "Please choose a different time slot."
                    ),
                }
        return None

    def book_appointment(
        self,
        patient_id: str,
        doctor_id: str,
        date: str,
        time_slot: str,
        reason: str = "",
        patient_name: str = "",
        doctor_name: str = "",
    ) -> Dict:
        """Books a new appointment and persists it to the JSON file."""
        appointments = self._load_appointments()

        # ── Double-booking guard ─────────────────────────────────────────────────
        conflict = self._check_conflicts(
            appointments, date, time_slot,
            patient_id=patient_id, doctor_id=doctor_id
        )
        if conflict:
            return conflict

        new_appt = {
            "appointment_id": self._generate_appointment_id(appointments),
            "patient_id": patient_id,
            "patient_name": patient_name or patient_id,
            "doctor_id": doctor_id,
            "doctor_name": doctor_name or doctor_id,
            "appointment_date": date,
            "time_slot": time_slot,
            "status": "Scheduled",
            "reason_for_visit": reason,
            "created_at": datetime.now().isoformat(),
        }
        appointments.append(new_appt)
        self._save_appointments(appointments)
        return {
            "status": "Success",
            "message": f"Appointment {new_appt['appointment_id']} booked successfully.",
            "appointment": new_appt,
        }

    def cancel_appointment(self, appointment_id: str) -> Dict:
        """Cancels an existing appointment by ID."""
        appointments = self._load_appointments()
        for appt in appointments:
            if appt.get("appointment_id") == appointment_id:
                appt["status"] = "Cancelled"
                appt["cancelled_at"] = datetime.now().isoformat()
                self._save_appointments(appointments)
                return {
                    "status": "Success",
                    "message": f"Appointment {appointment_id} has been cancelled.",
                    "appointment": appt,
                }
        return {"status": "Error", "message": f"Appointment {appointment_id} not found."}

    def reschedule_appointment(
        self, appointment_id: str, new_date: str, new_time_slot: str
    ) -> Dict:
        """Reschedules an appointment to a new date and time slot."""
        appointments = self._load_appointments()

        # Find the appointment to reschedule first
        target = next(
            (a for a in appointments if a.get("appointment_id") == appointment_id), None
        )
        if not target:
            return {"status": "Error", "message": f"Appointment {appointment_id} not found."}

        # ── Double-booking guard for new slot ────────────────────────────────────
        conflict = self._check_conflicts(
            appointments, new_date, new_time_slot,
            patient_id=target.get("patient_id", ""),
            doctor_id=target.get("doctor_id", ""),
            exclude_id=appointment_id,  # don't conflict with itself
        )
        if conflict:
            return conflict

        target["appointment_date"] = new_date
        target["time_slot"] = new_time_slot
        target["status"] = "Rescheduled"
        target["rescheduled_at"] = datetime.now().isoformat()
        self._save_appointments(appointments)
        return {
            "status": "Success",
            "message": f"Appointment {appointment_id} rescheduled to {new_date} at {new_time_slot}.",
            "appointment": target,
        }

    def list_appointments(self, patient_id: str = "", doctor_id: str = "") -> List[Dict]:
        """Lists appointments filtered by patient or doctor ID."""
        appointments = self._load_appointments()
        results = []
        for appt in appointments:
            patient_match = (
                appt.get("patient_id") == patient_id if patient_id else True
            )
            doctor_match = (
                appt.get("doctor_id") == doctor_id if doctor_id else True
            )
            if patient_match and doctor_match:
                results.append(appt)
        return results

    def get_appointment(self, appointment_id: str) -> Dict:
        """Retrieves a single appointment by ID."""
        appointments = self._load_appointments()
        for appt in appointments:
            if appt.get("appointment_id") == appointment_id:
                return appt
        return {"error": f"Appointment {appointment_id} not found."}