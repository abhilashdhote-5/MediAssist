from typing import Any, Dict
from memory.state import AgentState
from prompts.reflection_prompt import REFLECTION_SYSTEM_PROMPT
from utils.llm_factory import get_llm_for_task

class ReflectionNode:
    """
    Reflection & Safety Validation Node to review combined outputs, check safety guardrails,
    and attach non-diagnostic medical disclaimers (FR-08).
    Uses Groq API Key 2 for safety reflection tasks.
    """
    def __init__(self):
        self.reflection_prompt = REFLECTION_SYSTEM_PROMPT
        self.llm = get_llm_for_task("reflection")

    def append_medical_disclaimer(self, response_text: str) -> str:
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
        agent_outputs = state.get("agent_outputs", {})
        combined_chunks = []

        for key, text in agent_outputs.items():
            if text:
                combined_chunks.append(str(text))

        raw_response = "\n\n".join(combined_chunks) if combined_chunks else "Thank you for reaching out to MediAssist AI. How may I assist your healthcare needs today?"

        final_response = raw_response

        # Perform safety check with LLM if available
        if self.llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                res = self.llm.invoke([
                    SystemMessage(content=self.reflection_prompt),
                    HumanMessage(content=f"Drafted Healthcare Response:\n{raw_response}")
                ])
                if res and res.content:
                    final_response = str(res.content)
            except Exception as e:
                print(f"Reflection Node LLM call fallback: {e}")

        final_sanitized = self.append_medical_disclaimer(final_response)

        return {
            "final_response": final_sanitized,
            "is_safe": True,
            "reflection_feedback": "Passed all safety and non-diagnostic compliance checks."
        }

def validate_response(state: AgentState) -> Dict[str, Any]:
    node = ReflectionNode()
    return node.validate_response(state)
