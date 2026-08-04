import json
import os
from typing import Dict, Any
from memory.state import AgentState
from prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT

class SupervisorAgent:
    """
    Supervisor Agent responsible for classifying patient query intent and routing to specialized agents.
    """
    def __init__(self):
        self.prompt = SUPERVISOR_SYSTEM_PROMPT

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
        
        # Rule-based / Keyword intent fallback & detection logic
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
        """
        Conditional edge routing helper function for LangGraph.
        """
        return state.get("next_node", "symptom_agent")

def classify_intent(state: AgentState) -> Dict[str, Any]:
    supervisor = SupervisorAgent()
    return supervisor.classify_intent(state)

def route_next_node(state: AgentState) -> str:
    supervisor = SupervisorAgent()
    return supervisor.route_next_node(state)
