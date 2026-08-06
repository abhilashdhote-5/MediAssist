from typing import Dict, Any
from memory.state import AgentState
from utils.llm_factory import get_llm_for_task


GREETING_FALLBACKS = {
    "hi": "Hello! 👋 I'm MediAssist AI, your intelligent healthcare assistant. I can help you with:\n\n"
          "- 📅 **Appointments** — Book, reschedule or cancel doctor visits\n"
          "- 🩺 **Symptoms** — Get guidance on how you're feeling\n"
          "- 💊 **Medications** — Dosage, side effects & interactions\n"
          "- 📋 **Lab Reports** — Upload & understand your test results\n\n"
          "What can I help you with today?",
    "hello": "Hello! 👋 How are you doing today? I'm MediAssist AI and I'm here to help with your healthcare needs.\n\n"
             "You can ask me about appointments, symptoms, medications, or upload a lab report for analysis. What's on your mind?",
    "hey": "Hey there! 👋 I'm MediAssist AI. Feel free to ask me anything about your health, appointments, or medications!",
    "how are you": "I'm functioning perfectly and ready to assist you! 😊 How can I help with your health today?",
    "good morning": "Good morning! ☀️ Hope you're having a great day. I'm MediAssist AI — how can I assist you with your health today?",
    "good afternoon": "Good afternoon! 🌤️ I'm MediAssist AI, ready to help. What can I do for you today?",
    "good evening": "Good evening! 🌙 I'm MediAssist AI. How can I assist you with your health this evening?",
    "thanks": "You're welcome! 😊 Is there anything else I can help you with?",
    "thank you": "You're welcome! 😊 Feel free to ask if you have any other questions.",
    "bye": "Goodbye! 👋 Take care of your health. Come back anytime you need assistance!",
    "help": "Of course! 🤝 Here's how I can help:\n\n"
            "- 📅 **Appointments** — Book, reschedule or cancel visits\n"
            "- 🩺 **Symptoms** — Understand and get guidance on symptoms\n"
            "- 💊 **Medications** — Get dosage and interaction information\n"
            "- 📋 **Lab Reports** — Analyze and explain your test results\n\n"
            "Just describe what you need!",
}

GENERAL_SYSTEM_PROMPT = """You are MediAssist AI, a friendly and professional healthcare assistant.
The patient has sent a general conversational message (greeting, small talk, or general question).

Respond warmly and helpfully. Keep it brief (2-4 sentences). 
- Welcome them if it's a greeting
- Let them know you can help with appointments, symptoms, medications, and lab reports
- Invite them to ask their question
- MULTILINGUAL RESPONSE RULE: ALWAYS respond in the EXACT SAME language that the patient used (e.g. Hindi, Spanish, French, German, Marathi, Tamil, Telugu, etc.).

Do NOT provide any specific medical advice in this response.
"""


def handle_general_conversation(state: AgentState) -> Dict[str, Any]:
    """
    Handles general/greeting messages that don't need specialized medical routing.
    Returns a warm, helpful response without any clinical content.
    """
    messages = state.get("messages", [])
    last_user_message = ""
    from langchain_core.messages import HumanMessage
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_message = getattr(msg, "content", "").strip()
            if last_user_message:
                break

    # Check for exact/keyword matches first
    lower_msg = last_user_message.lower().strip().rstrip("!?.").strip()
    for keyword, response in GREETING_FALLBACKS.items():
        if lower_msg == keyword or lower_msg.startswith(keyword):
            return {
                "final_response": response,
                "current_intent": "general",
                "is_safe": True,
                "reflection_feedback": "",
            }

    # Use LLM for other general conversation
    llm = get_llm_for_task("supervisor")
    if llm:
        try:
            from langchain_core.messages import SystemMessage
            res = llm.invoke([
                SystemMessage(content=GENERAL_SYSTEM_PROMPT),
                HumanMessage(content=last_user_message)
            ])
            response_text = str(res.content).strip()
            if response_text:
                return {
                    "final_response": response_text,
                    "current_intent": "general",
                    "is_safe": True,
                    "reflection_feedback": "",
                }
        except Exception as e:
            print(f"General agent LLM error: {e}")

    # Final fallback
    return {
        "final_response": (
            "Hello! 👋 I'm MediAssist AI, your healthcare assistant. "
            "I can help you with appointments, symptoms, medications, and lab reports. "
            "What would you like to know today?"
        ),
        "current_intent": "general",
        "is_safe": True,
        "reflection_feedback": "",
    }
