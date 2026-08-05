import json
from typing import Dict, Any
from memory.state import AgentState
from prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT
from utils.llm_factory import get_llm_for_task

# Keywords that identify a general/greeting message vs a medical query
GREETING_KEYWORDS = {
    "hi", "hello", "hey", "hiya", "howdy", "greetings", "sup",
    "good morning", "good afternoon", "good evening", "good night",
    "how are you", "how r u", "how are u", "what's up", "whats up",
    "thanks", "thank you", "thank u", "ty", "thx", "cheers",
    "bye", "goodbye", "see you", "see ya", "later",
    "help", "what can you do", "what do you do",
    "who are you", "what are you",
}

# Words that even in short messages indicate a real medical query
MEDICAL_SIGNAL_WORDS = {
    "pain", "fever", "dose", "blood", "test", "book", "cancel",
    "medicine", "tablet", "report", "symptom", "cough", "dizzy",
    "appointment", "doctor", "prescription", "allergy", "drug",
}


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
        Analyzes the latest human user message in state to dynamically determine patient intent and next workflow node.
        Resets routing on every turn to prevent agent lock-in.
        """
        messages = state.get("messages", [])
        last_user_message = ""
        
        # Look specifically for the latest human user message
        for msg in reversed(messages):
            msg_type = getattr(msg, "type", None)
            role = getattr(msg, "role", None) if hasattr(msg, "role") else None
            
            from langchain_core.messages import HumanMessage
            if isinstance(msg, HumanMessage) or msg_type == "human" or role == "user":
                last_user_message = getattr(msg, "content", str(msg))
                if last_user_message:
                    break
        
        # Fallback to last message if no HumanMessage explicitly typed
        if not last_user_message and messages:
            last_msg = messages[-1]
            last_user_message = getattr(last_msg, "content", str(last_msg))

        user_text = last_user_message.lower().strip()

        # ── View-appointment intent guard (must run BEFORE greeting check & LLM) ────
        # These phrases clearly mean "show existing appointments", not "book new ones"
        VIEW_APPOINTMENT_KEYWORDS = [
            "show my appointment", "show appointment", "list appointment",
            "view appointment", "my appointment", "check appointment",
            "upcoming appointment", "past appointment", "appointment history",
            "what appointment", "see my appointment", "see appointment",
            "do i have appointment", "scheduled appointment", "booked appointment",
        ]
        if any(kw in user_text for kw in VIEW_APPOINTMENT_KEYWORDS):
            return {
                "current_intent": "view_appointment",
                "next_node": "view_appointment_agent",
                "agent_outputs": {}
            }

        # ── Greeting / General conversation detection ─────────────────────────────
        # Strip trailing punctuation for keyword matching
        cleaned = user_text.rstrip("!?.,").strip()

        # Exact match or starts-with for known greetings
        is_greeting = (
            cleaned in GREETING_KEYWORDS
            or any(cleaned.startswith(g) for g in GREETING_KEYWORDS)
        )

        # Also treat very short messages (≤3 words) with no medical signal as general
        has_medical_signal = any(w in user_text for w in MEDICAL_SIGNAL_WORDS)
        if not is_greeting and len(user_text.split()) <= 3 and not has_medical_signal:
            is_greeting = True

        if is_greeting:
            return {
                "current_intent": "general",
                "next_node": "general_agent",
                "agent_outputs": {}
            }
        
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
                    target_node = parsed.get("next_node", "symptom_agent")
                    target_intent = parsed.get("current_intent", "symptom")
                    valid_nodes = [
                        "appointment_agent", "view_appointment_agent", "symptom_agent",
                        "medication_agent", "report_agent", "general_agent"
                    ]
                    if target_node in valid_nodes:
                        return {
                            "current_intent": target_intent,
                            "next_node": target_node,
                            "agent_outputs": {}
                        }
            except Exception as e:
                print(f"Supervisor LLM classification fallback: {e}")

        # Rule-based fallback classification
        intent = "symptom"
        next_node = "symptom_agent"

        if any(w in user_text for w in ["appointment", "book", "reschedule", "cancel", "doctor", "slot", "schedule", "visit"]):
            intent = "appointment"
            next_node = "appointment_agent"
        elif any(w in user_text for w in ["medicine", "tablet", "dosage", "side effect", "pill", "paracetamol", "allergy", "drug", "prescription"]):
            intent = "medication"
            next_node = "medication_agent"
        elif any(w in user_text for w in ["report", "lab", "cbc", "blood", "test", "cholesterol", "lipid", "pdf", "results", "hemoglobin", "wbc"]):
            intent = "report"
            next_node = "report_agent"
        elif any(w in user_text for w in ["fever", "pain", "headache", "cough", "symptom", "cold", "sick", "nausea", "dizzy", "stomach"]):
            intent = "symptom"
            next_node = "symptom_agent"

        return {
            "current_intent": intent,
            "next_node": next_node,
            "agent_outputs": {}
        }

    def route_next_node(self, state: AgentState) -> str:
        return state.get("next_node", "symptom_agent")

def classify_intent(state: AgentState) -> Dict[str, Any]:
    supervisor = SupervisorAgent()
    return supervisor.classify_intent(state)

def route_next_node(state: AgentState) -> str:
    supervisor = SupervisorAgent()
    return supervisor.route_next_node(state)