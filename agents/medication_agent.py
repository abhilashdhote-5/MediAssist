from typing import Any, Dict
from memory.state import AgentState
from prompts.medication_prompt import MEDICATION_SYSTEM_PROMPT
from tools.medicine_lookup import MedicineLookupTool
from utils.helpers import load_json_file
from utils.llm_factory import get_llm_for_task

class MedicationAgent:
    """
    Medication Information Agent for drug details, dosages, and allergy checks (FR-03).
    Uses Groq API Key 1 for medication information tasks.
    """
    def __init__(self):
        self.system_prompt = MEDICATION_SYSTEM_PROMPT
        self.medicine_tool = MedicineLookupTool()
        self.llm = get_llm_for_task("medication")
        self.tools = [self.medicine_tool.query_medicine]

    def cross_check_allergy(self, medicine_name: str, patient_id: str) -> str:
        patients = load_json_file("data/patients.json", default=[])
        patient = next((p for p in patients if p.get("patient_id") == patient_id), {})
        allergies = patient.get("known_allergies", [])

        med_lower = medicine_name.lower()
        for allergy in allergies:
            if allergy.lower() in med_lower or med_lower in allergy.lower():
                return f"⚠️ **ALLERGY WARNING**: Patient {patient_id} has a known recorded allergy to '{allergy}'! Avoid administering this drug."
        
        return "✅ No conflicting patient allergies detected in EHR records."

    def get_medication_info(self, state: AgentState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_user_message = ""
        for msg in reversed(messages):
            content = getattr(msg, "content", str(msg))
            if content:
                last_user_message = content
                break

        patient_id = state.get("patient_id", "PAT8801")
        med_info = self.medicine_tool.query_medicine(last_user_message)
        allergy_status = self.cross_check_allergy(last_user_message, patient_id)

        if "brand_name" in med_info:
            output_text = (
                f"### Medication Information\n\n"
                f"💊 **Brand Name:** {med_info.get('brand_name')}\n"
                f"🧪 **Generic Name:** {med_info.get('generic_name')}\n"
                f"📂 **Category:** {med_info.get('category')}\n\n"
                f"🎯 **Purpose:** {med_info.get('purpose')}\n"
                f"📏 **Standard Dosage:** {med_info.get('standard_dosage')}\n\n"
                f"⚠️ **Precautions:**\n- " + "\n- ".join(med_info.get('precautions', [])) + "\n\n"
                f"🤢 **Potential Side Effects:**\n- " + "\n- ".join(med_info.get('side_effects', [])) + "\n\n"
                f"🛡️ **Allergy Status:** {allergy_status}"
            )
        else:
            output_text = f"### Medication Information\n\n{med_info.get('message')}\n\n🛡️ **Allergy Status:** {allergy_status}"

        # Enhance explanation with LLM if available
        if self.llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                res = self.llm.invoke([
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=f"Patient Query: {last_user_message}\nStructured Medication Data:\n{output_text}")
                ])
                if res and res.content:
                    output_text = str(res.content)
            except Exception as e:
                print(f"Medication Agent LLM call fallback: {e}")

        agent_outputs = state.get("agent_outputs", {})
        agent_outputs["medication_info"] = output_text

        return {
            "agent_outputs": agent_outputs,
            "next_node": "reflection_node"
        }

def get_medication_info(state: AgentState) -> Dict[str, Any]:
    agent = MedicationAgent()
    return agent.get_medication_info(state)
