from typing import Any, Dict, List
from memory.state import AgentState
from prompts.report_prompt import REPORT_SYSTEM_PROMPT
from tools.report_reader import ReportReaderTool
from utils.llm_factory import get_llm_for_task

class ReportAgent:
    """
    Medical Report Explanation Agent simplifying lab report PDFs & findings (FR-04).
    Uses Groq API Key 2 for report explanation tasks.
    """
    def __init__(self):
        self.system_prompt = REPORT_SYSTEM_PROMPT
        self.report_tool = ReportReaderTool()
        self.llm = get_llm_for_task("report")
        self.tools = [
            self.report_tool.extract_text_from_pdf,
            self.report_tool.get_structured_report
        ]

    def highlight_abnormalities(self, lab_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [res for res in lab_results if res.get("status") in ["High", "Low"]]

    def explain_lab_report(self, state: AgentState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_user_message = ""
        for msg in reversed(messages):
            content = getattr(msg, "content", str(msg))
            if content:
                last_user_message = content
                break

        report = self.report_tool.get_structured_report("REP5001")
        lab_results = report.get("lab_results", [])
        abnormalities = self.highlight_abnormalities(lab_results)

        explanation_lines = []
        explanation_lines.append(f"### Medical Report Explanation")
        explanation_lines.append(f"📋 **Report Type:** {report.get('report_type', 'Laboratory Report')}")
        explanation_lines.append(f"📅 **Report Date:** {report.get('report_date', 'Recent')}\n")

        explanation_lines.append("#### Summary of Parameters:")
        for res in lab_results:
            status_flag = f"🔴 **{res.get('status')}**" if res.get("status") != "Normal" else "🟢 Normal"
            explanation_lines.append(
                f"- **{res.get('parameter')}**: {res.get('value')} {res.get('unit')} (Reference: {res.get('reference_range')}) — {status_flag}"
            )

        if abnormalities:
            explanation_lines.append("\n⚠️ **Attention Areas (Abnormal Values):**")
            for ab in abnormalities:
                explanation_lines.append(
                    f"- **{ab.get('parameter')}** is **{ab.get('status')}** ({ab.get('value')} {ab.get('unit')}). Please discuss this finding with your attending physician."
                )
        else:
            explanation_lines.append("\n✅ All tested parameters fall within normal reference ranges.")

        output_text = "\n".join(explanation_lines)

        # Enhance with LLM if available
        if self.llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                res = self.llm.invoke([
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=f"Patient Query: {last_user_message}\nLab Results Data:\n{output_text}")
                ])
                if res and res.content:
                    output_text = str(res.content)
            except Exception as e:
                print(f"Report Agent LLM call fallback: {e}")

        agent_outputs = state.get("agent_outputs", {})
        agent_outputs["report_explanation"] = output_text

        return {
            "agent_outputs": agent_outputs,
            "next_node": "reflection_node"
        }

def explain_lab_report(state: AgentState) -> Dict[str, Any]:
    agent = ReportAgent()
    return agent.explain_lab_report(state)
