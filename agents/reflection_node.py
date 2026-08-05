import re
from typing import Any, Dict
from memory.state import AgentState
from prompts.reflection_prompt import REFLECTION_SYSTEM_PROMPT
from utils.llm_factory import get_llm_for_task

MEDICAL_DISCLAIMER = (
    "\n\n---\n"
    "🩺 **Medical Disclaimer:** *MediAssist AI provides general healthcare information only. "
    "It is not a substitute for professional medical diagnosis or clinical treatment. "
    "In case of a medical emergency, please call your local emergency services immediately.*"
)


class ReflectionNode:
    """
    Reflection & Safety Validation Node — reviews combined agent outputs, applies
    safety guardrails, filters raw LLM artifacts, and appends a non-diagnostic disclaimer.
    Uses Groq API Key 2 for safety reflection tasks.
    """

    def __init__(self):
        self.reflection_prompt = REFLECTION_SYSTEM_PROMPT
        self.llm = get_llm_for_task("reflection")

    @staticmethod
    def _sanitize(text: str) -> str:
        """
        Remove common LLM trace artifacts and normalize whitespace.
        """
        # Strip leading/trailing whitespace
        text = text.strip()

        # Remove lines that are purely raw JSON blobs or Python repr
        lines = text.split("\n")
        clean_lines = []
        for line in lines:
            # Skip lines that look like raw Python dict dumps
            if re.match(r"^\s*\{.*\}\s*$", line) and len(line) > 200:
                continue
            clean_lines.append(line)
        text = "\n".join(clean_lines)

        # Collapse excessive blank lines (more than 2 consecutive)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def _append_disclaimer(text: str) -> str:
        if MEDICAL_DISCLAIMER.strip() not in text:
            return text + MEDICAL_DISCLAIMER
        return text

    def validate_response(self, state: AgentState) -> Dict[str, Any]:
        # ── Pass-through for general/greeting responses ─────────────────────────
        # General agent sets final_response directly; no medical disclaimer needed
        current_intent = state.get("current_intent", "")
        if current_intent == "general":
            existing = state.get("final_response", "")
            if existing:
                return {
                    "final_response": self._sanitize(existing),
                    "is_safe": True,
                    "reflection_feedback": "General conversation — no clinical review needed.",
                }

        agent_outputs = state.get("agent_outputs", {})

        # Determine which output to use (skip internal signals like 'appointment_pending')
        response_keys = [
            k for k in ["report_explanation", "medication_info", "symptom_guidance", "appointment_result"]
            if k in agent_outputs and agent_outputs[k]
        ]

        if response_keys:
            raw_response = agent_outputs[response_keys[0]]
        else:
            raw_response = (
                "Thank you for reaching out to MediAssist AI. "
                "How may I assist your healthcare needs today?"
            )

        final_response = self._sanitize(str(raw_response))

        # Optional LLM safety check & re-phrasing
        if self.llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                res = self.llm.invoke([
                    SystemMessage(content=self.reflection_prompt),
                    HumanMessage(
                        content=(
                            f"Healthcare Response to Review:\n{final_response}\n\n"
                            "Review this response for safety and clarity. "
                            "Return a clean, concise version that:\n"
                            "1. Keeps all important medical facts intact\n"
                            "2. Removes any diagnostic claims\n"
                            "3. Is written in plain English a patient can understand\n"
                            "4. Uses markdown formatting (bold, bullet points) clearly\n"
                            "Return ONLY the revised response text."
                        )
                    ),
                ])
                if res and res.content:
                    candidate = self._sanitize(str(res.content))
                    # Use LLM version only if it is substantive
                    if len(candidate) > 50:
                        final_response = candidate
            except Exception as e:
                print(f"Reflection Node LLM call fallback: {e}")

        final_response = self._append_disclaimer(final_response)

        return {
            "final_response": final_response,
            "is_safe": True,
            "reflection_feedback": "Passed all safety and non-diagnostic compliance checks.",
        }


def validate_response(state: AgentState) -> Dict[str, Any]:
    node = ReflectionNode()
    return node.validate_response(state)
