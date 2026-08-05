from typing import Any, Dict
from memory.state import AgentState
from tools.appointment_tool import AppointmentTool
from utils.helpers import load_json_file


class ViewAppointmentAgent:
    """
    Read-only agent that retrieves and formats a patient's existing appointments.
    No HITL needed — this is a pure read/display operation.
    """

    def __init__(self):
        self.tool = AppointmentTool()

    def _get_patient_name(self, patient_id: str) -> str:
        patients = load_json_file("data/patients.json", default=[])
        patient = next((p for p in patients if p.get("patient_id") == patient_id), {})
        return patient.get("full_name", patient_id)

    def _format_status_badge(self, status: str) -> str:
        badges = {
            "Scheduled": "🟢 Scheduled",
            "Rescheduled": "🔵 Rescheduled",
            "Cancelled": "🔴 Cancelled",
            "Completed": "✅ Completed",
        }
        return badges.get(status, f"• {status}")

    def view_appointments(self, state: AgentState) -> Dict[str, Any]:
        patient_id = state.get("patient_id", "")
        patient_name = self._get_patient_name(patient_id)

        appointments = self.tool.list_appointments(patient_id=patient_id)

        if not appointments:
            response = (
                f"📋 **No appointments found** for **{patient_name}**.\n\n"
                "You haven't booked any appointments yet. "
                "Would you like me to help you schedule one? Just say **'book an appointment'**!"
            )
            return {
                "final_response": response,
                "current_intent": "view_appointment",
                "is_safe": True,
                "reflection_feedback": "",
            }

        # Sort by date descending for upcoming first
        def sort_key(a):
            return a.get("appointment_date", ""), a.get("time_slot", "")

        sorted_appts = sorted(appointments, key=sort_key, reverse=False)
        scheduled = [a for a in sorted_appts if a.get("status") not in ("Cancelled",)]
        cancelled = [a for a in sorted_appts if a.get("status") == "Cancelled"]

        lines = [f"📋 **Appointments for {patient_name}**\n"]

        if scheduled:
            lines.append(f"**Active / Upcoming ({len(scheduled)})**\n")
            for appt in scheduled:
                lines.append(
                    f"---\n"
                    f"**{self._format_status_badge(appt.get('status', 'Scheduled'))}**  "
                    f"· ID: `{appt.get('appointment_id', 'N/A')}`\n"
                    f"🩺 **Doctor:** {appt.get('doctor_name', 'N/A')}\n"
                    f"📅 **Date:** {appt.get('appointment_date', 'N/A')}"
                    f"  ·  🕐 **Time:** {appt.get('time_slot', 'N/A')}\n"
                    f"📝 **Reason:** {appt.get('reason_for_visit', 'General consultation')}\n"
                )

        if cancelled:
            lines.append(f"\n**Cancelled ({len(cancelled)})**\n")
            for appt in cancelled:
                lines.append(
                    f"- ~~{appt.get('appointment_date', 'N/A')} · {appt.get('doctor_name', 'N/A')}~~ "
                    f"(ID: `{appt.get('appointment_id', 'N/A')}`)\n"
                )

        lines.append(
            "\n---\n"
            "💬 You can say **'reschedule my appointment'**, **'cancel my appointment'**, "
            "or **'book a new appointment'** to manage your visits."
        )

        return {
            "final_response": "\n".join(lines),
            "current_intent": "view_appointment",
            "is_safe": True,
            "reflection_feedback": "",
        }


def view_appointments(state: AgentState) -> Dict[str, Any]:
    agent = ViewAppointmentAgent()
    return agent.view_appointments(state)
