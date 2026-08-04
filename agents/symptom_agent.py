from typing import Any, Dict, List
from memory.state import AgentState
from prompts.symptom_prompt import SYMPTOM_SYSTEM_PROMPT
from utils.helpers import load_json_file

class SymptomAgent:
    """
    Symptom Assessment Agent providing non-diagnostic healthcare guidance (FR-02).
    """
    def __init__(self):
        self.system_prompt = SYMPTOM_SYSTEM_PROMPT
        self.knowledge_base_path = "data/symptom_knowledge.json"

    def check_red_flags(self, symptoms: List[str]) -> bool:
        """
        Scans symptoms list for critical emergency warning indicators.
        """
        critical_keywords = ["chest pain", "shortness of breath", "stiff neck", "unconscious", "severe bleeding", "103°f"]
        for symptom in symptoms:
            if any(kw in symptom.lower() for kw in critical_keywords):
                return True
        return False

    def assess_symptoms(self, state: AgentState) -> Dict[str, Any]:
        """
        Matches symptoms against knowledge base and produces care guidance.
        """
        messages = state.get("messages", [])
        last_user_message = ""
        for msg in reversed(messages):
            content = getattr(msg, "content", str(msg))
            if content:
                last_user_message = content
                break

        symptoms_knowledge = load_json_file(self.knowledge_base_path, default=[])
        user_text = last_user_message.lower()

        matched_item = None
        for item in symptoms_knowledge:
            if any(word in user_text for word in item.get("primary_symptom", "").lower().split()):
                matched_item = item
                break

        if not matched_item and symptoms_knowledge:
            matched_item = symptoms_knowledge[0]

        is_critical = self.check_red_flags([user_text]) or matched_item.get("risk_level") == "Critical"

        if is_critical:
            guidance_text = (
                f"⚠️ **EMERGENCY WARNING**: Your symptoms may indicate a critical medical situation.\n\n"
                f"🚨 **Red Flag Indicators:** {', '.join(matched_item.get('red_flags', []))}\n\n"
                f"**Recommendation:** Please seek immediate emergency medical care or visit the nearest hospital emergency room."
            )
        else:
            guidance_text = (
                f"### Symptom Assessment & Care Guidance\n\n"
                f"🔹 **Primary Condition Identified:** {matched_item.get('primary_symptom')}\n"
                f"🔹 **Risk Level:** {matched_item.get('risk_level')}\n"
                f"🔹 **Care Guidance:** {matched_item.get('care_guidance')}\n"
                f"🩺 **Recommended Specialist:** {matched_item.get('recommended_specialty')}\n\n"
                f"⚠️ *If your symptoms worsen or persist beyond 48 hours, please consult a registered medical professional.*"
            )

        agent_outputs = state.get("agent_outputs", {})
        agent_outputs["symptom_guidance"] = guidance_text

        return {
            "agent_outputs": agent_outputs,
            "next_node": "reflection_node"
        }

def assess_symptoms(state: AgentState) -> Dict[str, Any]:
    agent = SymptomAgent()
    return agent.assess_symptoms(state)
