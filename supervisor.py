import json
from typing import Dict, Any
from memory.state import AgentState
from prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT
from utils.llm_factory import get_llm_for_task

class SupervisorAgent:
    """
    Supervisor Agent responsible for classifying patient query intent and routing to specialized agents.
    Uses Groq API Key 1 for intent routing tasks.
    """
    def __init__(self):
        self.prompt = SUPERVISOR_SYSTEM_PROMPT
        self.llm = get_llm_for_task("supervisor")

    def classify_intent(self, state: AgentState) -> Dict[str, Any]:
        """
        Analyzes recent conversation messages in state to determine patient intent and next workflow node.
        """
        messages = state.get("messages", [])
        last_user_message = ""
        for msg in reversed(messages):
            content = getattr(msg, "content", str(msg))
            if content:
                last_user_message = content
                break

        user_text = last_user_message.lower()
        
        # Try LLM classification first if Groq LLM is available
        if self.llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                res = self.llm.invoke([
                    SystemMessage(content=self.prompt),
                    HumanMessage(content=f"Patient Message: {last_user_message}")
                ])
                content = str(res.content)
                if "{" in content and "}" in content:
                    json_str = content[content.find("{"):content.rfind("}")+1]
                    parsed = json.loads(json_str)
                    return {
                        "current_intent": parsed.get("current_intent", "symptom"),
                        "next_node": parsed.get("next_node", "symptom_agent")
                    }
            except Exception as e:
                print(f"Supervisor LLM classification fallback: {e}")

        # Rule-based fallback classification
        intent = "symptom"
        next_node = "symptom_agent"

        if any(w in user_text for w in ["appointment", "book", "reschedule", "cancel", "doctor", "slot", "schedule"]):
            intent = "appointment"
            next_node = "appointment_agent"
        elif any(w in user_text for w in ["medicine", "tablet", "dosage", "side effect", "pill", "paracetamol", "allergy", "drug"]):
            intent = "medication"
            next_node = "medication_agent"
        elif any(w in user_text for w in ["report", "lab", "cbc", "blood", "test", "cholesterol", "lipid", "pdf"]):
            intent = "report"
            next_node = "report_agent"
        elif any(w in user_text for w in ["fever", "pain", "headache", "cough", "symptom", "cold", "sick"]):
            intent = "symptom"
            next_node = "symptom_agent"

        return {
            "current_intent": intent,
            "next_node": next_node
        }

    def route_next_node(self, state: AgentState) -> str:
        return state.get("next_node", "symptom_agent")

def classify_intent(state: AgentState) -> Dict[str, Any]:
    supervisor = SupervisorAgent()
    return supervisor.classify_intent(state)

def route_next_node(state: AgentState) -> str:
    supervisor = SupervisorAgent()
    return supervisor.route_next_node(state)
