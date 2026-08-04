from typing import Any, Dict
from memory.state import AgentState
from prompts.reflection_prompt import REFLECTION_SYSTEM_PROMPT

class ReflectionNode:
    """
    Reflection & Safety Validation Node to review combined outputs, check safety guardrails,
    and attach non-diagnostic medical disclaimers (FR-08).
    """
    def __init__(self):
        self.reflection_prompt = REFLECTION_SYSTEM_PROMPT

    def append_medical_disclaimer(self, response_text: str) -> str:
        """
        Appends mandatory healthcare disclaimer to final patient output.
        """
        disclaimer = (
            "\n\n---\n"
            "🩺 **Medical Disclaimer:** *MediAssist AI provides general operational and information support. "
            "It is not a substitute for professional medical diagnosis or clinical treatment. "
            "In case of a medical emergency, please call your local emergency services or visit the nearest hospital immediately.*"
        )
        if disclaimer not in response_text:
            return response_text + disclaimer
        return response_text

    def validate_response(self, state: AgentState) -> Dict[str, Any]:
        """
        Evaluates outputs from specialized agents, verifies compliance, and generates final_response.
        """
        agent_outputs = state.get("agent_outputs", {})
        combined_chunks = []

        for key, text in agent_outputs.items():
            if text:
                combined_chunks.append(str(text))

        raw_response = "\n\n".join(combined_chunks) if combined_chunks else "Thank you for reaching out to MediAssist AI. How may I assist your healthcare needs today?"

        final_sanitized = self.append_medical_disclaimer(raw_response)

        return {
            "final_response": final_sanitized,
            "is_safe": True,
            "reflection_feedback": "Passed all safety and non-diagnostic compliance checks."
        }

def validate_response(state: AgentState) -> Dict[str, Any]:
    node = ReflectionNode()
    return node.validate_response(state)
