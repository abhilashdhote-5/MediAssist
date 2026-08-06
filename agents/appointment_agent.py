from typing import Any, Dict
from memory.state import AgentState
from prompts.appointment_prompt import APPOINTMENT_SYSTEM_PROMPT
from tools.appointment_tool import AppointmentTool
from tools.doctor_lookup import DoctorLookupTool
from utils.helpers import load_json_file
from utils.llm_factory import get_llm_for_task


class AppointmentAgent:
    """
    Appointment Management Agent for handling doctor appointment requests (FR-01).
    Reads doctor data from data/doctors.json and persists appointments to data/appointments.json.
    Uses Groq API Key 1 for appointment management tasks.
    """

    def __init__(self):
        self.system_prompt = APPOINTMENT_SYSTEM_PROMPT
        self.appointment_tool = AppointmentTool()
        self.doctor_tool = DoctorLookupTool()
        self.llm = get_llm_for_task("appointment")

    def _get_patient_name(self, patient_id: str) -> str:
        patients = load_json_file("data/patients.json", default=[])
        patient = next((p for p in patients if p.get("patient_id") == patient_id), {})
        return patient.get("full_name", patient_id)

    def extract_booking_details(self, user_text: str, patient_id: str) -> Dict[str, Any]:
        text_lower = user_text.lower()

        # Determine action
        action = "book"
        if "delete" in text_lower or "remove" in text_lower or "erase" in text_lower:
            action = "delete"
        elif "cancel" in text_lower:
            action = "cancel"
        elif "reschedule" in text_lower:
            action = "reschedule"

        # Try to find a specialty hint from the user query
        specialty_keywords = {
            "heart": "Cardiology", "cardiac": "Cardiology", "cardiology": "Cardiology",
            "skin": "Dermatology", "dermatology": "Dermatology",
            "child": "Pediatrics", "pediatric": "Pediatrics", "paediatric": "Pediatrics",
            "bone": "Orthopedics", "orthopedic": "Orthopedics",
            "diabetes": "Endocrinology", "thyroid": "Endocrinology", "endocrinology": "Endocrinology",
            "neuro": "Neurology", "brain": "Neurology",
            "general": "General Medicine",
        }

        specialty = "General Medicine"
        for kw, spec in specialty_keywords.items():
            if kw in text_lower:
                specialty = spec
                break

        # Find matching doctors from real data
        # Gather matching doctors (preserve full list for HITL selection)
        doctors = self.doctor_tool.search_doctors(specialty=specialty)
        if not doctors:
            doctors = self.doctor_tool.search_doctors()

        # Build a conservative default selection (first match) but keep full list
        selected_doctor = doctors[0] if doctors else {}

        # Normalize doctor dicts for UI consumption
        available_doctors = []
        for d in doctors:
            available_doctors.append({
                "doctor_id": d.get("doctor_id", "DOC001"),
                "full_name": d.get("full_name", "General Physician"),
                "qualification": d.get("qualification", "MBBS"),
                "experience_years": d.get("experience_years", 0),
                "consultation_fee": d.get("consultation_fee", 0),
                "currency": d.get("currency", "USD"),
                "available_slots": d.get("available_slots", ["09:00 AM", "11:30 AM", "02:00 PM"]),
                "available_days": d.get("available_days", []),
            })

        return {
            "action": action,
            "specialty": specialty,
            "doctor_id": selected_doctor.get("doctor_id", "DOC001"),
            "doctor_name": selected_doctor.get("full_name", "General Physician"),
            "qualification": selected_doctor.get("qualification", "MBBS"),
            "experience_years": selected_doctor.get("experience_years", 0),
            "consultation_fee": selected_doctor.get("consultation_fee", 0),
            "currency": selected_doctor.get("currency", "USD"),
            "available_slots": selected_doctor.get("available_slots", ["09:00 AM"]),
            "available_days": selected_doctor.get("available_days", []),
            "date": "2026-08-10",
            "time_slot": selected_doctor.get("available_slots", ["09:00 AM"])[0],
            "patient_id": patient_id,
            "patient_name": self._get_patient_name(patient_id),
            # expose full doctor list for UI HITL
            "available_doctors": available_doctors,
        }

    def process_appointment(self, state: AgentState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_user_message = ""
        for msg in reversed(messages):
            from langchain_core.messages import HumanMessage
            if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human" or getattr(msg, "role", "") == "user":
                last_user_message = getattr(msg, "content", str(msg))
                if last_user_message:
                    break
        if not last_user_message and messages:
            last_user_message = getattr(messages[-1], "content", str(messages[-1]))

        patient_id = state.get("patient_id", "PAT8801")
        details = self.extract_booking_details(last_user_message, patient_id)

        # Build a concise plain-English summary (HITL pending_action for UI)
        pending_action = {
            "action": details["action"],
            "doctor_name": details["doctor_name"],
            "specialty": details["specialty"],
            "date": details["date"],
            "time_slot": details["time_slot"],
            "patient_name": details["patient_name"],
            "patient_id": patient_id,
            "doctor_id": details["doctor_id"],
            "available_slots": details["available_slots"],
            "available_days": details["available_days"],
            "consultation_fee": details["consultation_fee"],
            "currency": details["currency"],
        }
        # Include the full list of matching doctors for HITL selection
        pending_action["available_doctors"] = details.get("available_doctors", [])

        # Signal to UI that HITL confirmation is needed
        agent_outputs = state.get("agent_outputs", {})
        agent_outputs["appointment_pending"] = pending_action
        agent_outputs["appointment_result"] = (
            f"I found **{details['doctor_name']}** ({details['specialty']}, {details['experience_years']} yrs exp).\n\n"
            f"📅 **Available Days:** {', '.join(details['available_days'])}\n"
            f"🕐 **Available Slots:** {', '.join(details['available_slots'])}\n"
            f"💰 **Consultation Fee:** {details['currency']} {details['consultation_fee']}\n\n"
            f"Please confirm the appointment details below to proceed."
        )

        return {
            "agent_outputs": agent_outputs,
            "next_node": "reflection_node",
        }


def process_appointment(state: AgentState) -> Dict[str, Any]:
    agent = AppointmentAgent()
    return agent.process_appointment(state)
