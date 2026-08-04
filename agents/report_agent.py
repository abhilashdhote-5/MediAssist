from typing import Any, Dict, List
from memory.state import AgentState
from prompts.report_prompt import REPORT_SYSTEM_PROMPT
from tools.report_reader import ReportReaderTool
from utils.helpers import load_json_file
from utils.llm_factory import get_llm_for_task


class ReportAgent:
    """
    Medical Report Explanation Agent simplifying lab report PDFs & findings (FR-04).
    Reads report data from data/medical_reports.json filtered by patient_id.
    Uses Groq API Key 2 for report explanation tasks.
    """

    def __init__(self):
        self.system_prompt = REPORT_SYSTEM_PROMPT
        self.report_tool = ReportReaderTool()
        self.llm = get_llm_for_task("report")

    def _get_patient_report(self, patient_id: str) -> Dict:
        """Get the most recent report for the current patient, or fall back to REP5001."""
        reports = self.report_tool.get_reports_for_patient(patient_id)
        if reports:
            # Return the most recent report (last by date)
            return sorted(reports, key=lambda r: r.get("report_date", ""), reverse=True)[0]
        # Fallback to first available report
        return self.report_tool.get_structured_report("REP5001")

    def explain_lab_report(self, state: AgentState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_user_message = ""
        for msg in reversed(messages):
            content = getattr(msg, "content", str(msg))
            if content:
                last_user_message = content
                break

        patient_id = state.get("patient_id", "PAT8801")

        # Try to extract a specific report ID from the message
        report = None
        user_upper = last_user_message.upper()
        if "REP" in user_upper:
            # Parse report ID from message like "explain REP5003"
            import re
            match = re.search(r"REP\d+", user_upper)
            if match:
                report = self.report_tool.get_structured_report(match.group())

        if not report or "error" in report:
            report = self._get_patient_report(patient_id)

        if "error" in report:
            output_text = (
                f"### 📋 Medical Report\n\nNo lab reports found for patient {patient_id}. "
                "Please upload your report or provide a report ID."
            )
        else:
            lab_results = report.get("lab_results", [])
            abnormalities = self.report_tool.highlight_abnormalities(lab_results)

            lines = [
                f"### 📋 Medical Report — {report.get('report_type', 'Lab Report')}",
                f"**Patient ID:** {report.get('patient_id')}  |  "
                f"**Date:** {report.get('report_date', 'Recent')}  |  "
                f"**Report ID:** {report.get('report_id')}",
                "",
                "#### Parameter Results:",
            ]

            for res in lab_results:
                status = res.get("status", "Unknown")
                if status == "Normal":
                    flag = "🟢 Normal"
                elif status == "High":
                    flag = "🔴 HIGH"
                elif status == "Low":
                    flag = "🟡 LOW"
                else:
                    flag = f"⚪ {status}"

                lines.append(
                    f"- **{res.get('parameter')}**: {res.get('value')} {res.get('unit')} "
                    f"(Ref: {res.get('reference_range')}) — {flag}"
                )

            if abnormalities:
                lines.append("\n⚠️ **Values Requiring Attention:**")
                for ab in abnormalities:
                    lines.append(
                        f"- **{ab.get('parameter')}** is **{ab.get('status')}** "
                        f"({ab.get('value')} {ab.get('unit')}). "
                        "Please discuss this with your doctor."
                    )
            else:
                lines.append("\n✅ All tested parameters fall within normal reference ranges.")

            output_text = "\n".join(lines)

        # Enhance with LLM for patient-friendly language
        if self.llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                res = self.llm.invoke([
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(
                        content=(
                            f"Patient Query: {last_user_message}\n"
                            f"Lab Results:\n{output_text}\n\n"
                            "Explain these results in plain, simple language a patient can understand. "
                            "Highlight any abnormal values clearly. Keep it concise and non-diagnostic."
                        )
                    ),
                ])
                if res and res.content:
                    output_text = str(res.content)
            except Exception as e:
                print(f"Report Agent LLM call fallback: {e}")

        agent_outputs = state.get("agent_outputs", {})
        agent_outputs["report_explanation"] = output_text

        return {
            "agent_outputs": agent_outputs,
            "next_node": "reflection_node",
        }


def explain_lab_report(state: AgentState) -> Dict[str, Any]:
    agent = ReportAgent()
    return agent.explain_lab_report(state)
