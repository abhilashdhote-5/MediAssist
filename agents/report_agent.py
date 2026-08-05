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
            from langchain_core.messages import HumanMessage
            if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human" or getattr(msg, "role", "") == "user":
                last_user_message = getattr(msg, "content", str(msg))
                if last_user_message:
                    break
        if not last_user_message and messages:
            last_user_message = getattr(messages[-1], "content", str(messages[-1]))

        patient_id = state.get("patient_id", "PAT8801")
        pdf_context = state.get("pdf_context", "")

        # Check if RAG PDF context is provided for uploaded lab reports
        if pdf_context and pdf_context.strip():
            output_text = ""
            if self.llm:
                try:
                    from langchain_core.messages import SystemMessage, HumanMessage
                    prompt_input = (
                        f"Patient Query: {last_user_message}\n\n"
                        f"EXTRACTED LAB REPORT RAG CONTEXT:\n{pdf_context}\n\n"
                        "Instructions:\n"
                        "1. Extract key health parameters/metrics, their values, units, and reference ranges found in the context.\n"
                        "2. Rely on your inherent medical knowledge to evaluate the metrics and highlight any values that are out of bounds (HIGH or LOW) or abnormal.\n"
                        "3. Present the results in a clean structured format with clear headings and bullet points.\n"
                        "4. If information is missing or unclear, state 'I don't know based on the provided report context' rather than guessing."
                    )
                    res = self.llm.invoke([
                        SystemMessage(content=self.system_prompt),
                        HumanMessage(content=prompt_input)
                    ])
                    if res and res.content:
                        output_text = str(res.content)
                except Exception as e:
                    print(f"Report Agent RAG LLM call fallback: {e}")

            if not output_text:
                output_text = (
                    f"### 📋 Uploaded Lab Report Analysis\n\n"
                    f"**Extracted Content Preview:**\n{pdf_context[:500]}...\n\n"
                    f"Please consult a physician to review these laboratory results in detail."
                )

            agent_outputs = state.get("agent_outputs", {})
            agent_outputs["report_explanation"] = output_text
            return {
                "agent_outputs": agent_outputs,
                "next_node": "reflection_node",
            }

        # Otherwise, process structured report database entries
        report = None
        user_upper = last_user_message.upper()
        if "REP" in user_upper:
            import re
            match = re.search(r"REP\d+", user_upper)
            if match:
                report = self.report_tool.get_structured_report(match.group())

        if not report or "error" in report:
            report = self._get_patient_report(patient_id)

        if "error" in report:
            output_text = (
                f"### 📋 Medical Report\n\nNo lab reports found for patient {patient_id}. "
                "Please upload your medical report PDF using the upload button beside the chatbox."
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
