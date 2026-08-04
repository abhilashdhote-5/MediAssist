from typing import Any, Dict
from memory.state import AgentState
from prompts.appointment_prompt import APPOINTMENT_SYSTEM_PROMPT
from tools.appointment_tool import AppointmentTool
from tools.doctor_lookup import DoctorLookupTool
from utils.llm_factory import get_llm_for_task

class AppointmentAgent:
    """
    Appointment Management Agent for handling doctor appointment requests (FR-01).
    Uses Groq API Key 1 for appointment management tasks.
    """
    def __init__(self):
        self.system_prompt = APPOINTMENT_SYSTEM_PROMPT
        self.appointment_tool = AppointmentTool()
        self.doctor_tool = DoctorLookupTool()
        self.llm = get_llm_for_task("appointment")
        self.tools = [
            self.appointment_tool.book_appointment,
            self.appointment_tool.reschedule_appointment,
            self.appointment_tool.cancel_appointment,
            self.doctor_tool.search_doctors
        ]

    def extract_booking_details(self, user_text: str) -> Dict[str, Any]:
        text = user_text.lower()
        action = "book"
        if "cancel" in text:
            action = "cancel"
        elif "reschedule" in text:
            action = "reschedule"

        doctors = self.doctor_tool.search_doctors()
        selected_doctor = doctors[0] if doctors else {}

        return {
            "action": action,
            "doctor_id": selected_doctor.get("doctor_id", "DOC001"),
            "doctor_name": selected_doctor.get("full_name", "Dr. Sarah Jenkins"),
            "specialty": selected_doctor.get("specialty", "General Medicine"),
            "date": "2026-08-10",
            "time_slot": "09:00 AM",
            "available_slots": selected_doctor.get("available_slots", ["09:00 AM", "11:30 AM", "02:00 PM"])
        }

    def process_appointment(self, state: AgentState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_user_message = ""
        for msg in reversed(messages):
            content = getattr(msg, "content", str(msg))
            if content:
                last_user_message = content
                break

        patient_id = state.get("patient_id", "PAT8801")
        details = self.extract_booking_details(last_user_message)
        
        if details["action"] == "cancel":
            res = self.appointment_tool.cancel_appointment("APT1001")
            response_text = res.get("message", "Appointment cancelled.")
        elif details["action"] == "reschedule":
            res = self.appointment_tool.reschedule_appointment("APT1001", details["date"], details["time_slot"])
            response_text = res.get("message", "Appointment rescheduled.")
        else:
            res = self.appointment_tool.book_appointment(
                patient_id=patient_id,
                doctor_id=details["doctor_id"],
                date=details["date"],
                time_slot=details["time_slot"],
                reason=last_user_message
            )
            response_text = (
                f"### Appointment Management Response\n\n"
                f"I have checked the availability for **{details['doctor_name']}** ({details['specialty']}).\n\n"
                f"📅 **Available Slots:** {', '.join(details['available_slots'])}\n\n"
                f"✅ **Status:** {res.get('message')}"
            )

        agent_outputs = state.get("agent_outputs", {})
        agent_outputs["appointment_result"] = response_text

        return {
            "agent_outputs": agent_outputs,
            "next_node": "reflection_node"
        }

def process_appointment(state: AgentState) -> Dict[str, Any]:
    agent = AppointmentAgent()
    return agent.process_appointment(state)
