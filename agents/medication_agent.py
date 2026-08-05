from typing import Any, Dict
from memory.state import AgentState
from prompts.medication_prompt import MEDICATION_SYSTEM_PROMPT
from tools.medicine_lookup import MedicineLookupTool
from utils.helpers import load_json_file
from utils.llm_factory import get_llm_for_task


class MedicationAgent:
    """
    Medication Information Agent for drug details, dosages, and allergy checks (FR-03).
    Reads medicine data from data/medicines.json and patient data from data/patients.json.
    Uses Groq API Key 1 for medication information tasks.
    """

    def __init__(self):
        self.system_prompt = MEDICATION_SYSTEM_PROMPT
        self.medicine_tool = MedicineLookupTool()
        self.llm = get_llm_for_task("medication")

    def cross_check_allergy(self, medicine_name: str, patient_id: str) -> str:
        """Cross-check patient known allergies from data/patients.json against medicine."""
        patients = load_json_file("data/patients.json", default=[])
        patient = next((p for p in patients if p.get("patient_id") == patient_id), {})
        allergies = patient.get("known_allergies", [])
        chronic_conditions = patient.get("chronic_conditions", [])

        med_lower = medicine_name.lower()
        for allergy in allergies:
            if allergy.lower() in med_lower or med_lower in allergy.lower():
                return (
                    f"⚠️ **ALLERGY WARNING**: Patient **{patient.get('full_name', patient_id)}** "
                    f"has a known recorded allergy to **'{allergy}'**! "
                    f"Do NOT administer this drug without consulting the attending physician."
                )

        # Check chronic conditions for medication interaction hints
        condition_warnings = []
        if any("diabetes" in c.lower() for c in chronic_conditions):
            if any(w in med_lower for w in ["steroid", "cortisone", "prednisolone"]):
                condition_warnings.append("may affect blood sugar levels (patient has diabetes)")
        if any("hypertension" in c.lower() for c in chronic_conditions):
            if any(w in med_lower for w in ["ibuprofen", "naproxen", "nsaid"]):
                condition_warnings.append("NSAIDs can elevate blood pressure (patient has hypertension)")

        if condition_warnings:
            return f"⚠️ **Caution**: {'; '.join(condition_warnings)}. Consult physician before use."

        return "✅ No conflicting allergies detected in patient EHR records."

    def get_medication_info(self, state: AgentState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_user_message = ""
        for msg in reversed(messages):
            from langchain_core.messages import HumanMessage
            if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human" or getattr(msg, "role", "") == "user":
                last_user_message = getattr(msg, "content", str(msg))
                if last_user_message:
                    break
        if not last_user_message and messages:
            last_user_message = getattr(messages[-1], "content", str(messages[-1]))

        patient_id = state.get("patient_id", "PAT8801")

        # Look up medicine from real data
        med_info = self.medicine_tool.query_medicine(last_user_message)
        allergy_status = self.cross_check_allergy(last_user_message, patient_id)

        if "brand_name" in med_info:
            output_text = (
                f"### 💊 Medication Information\n\n"
                f"**Brand Name:** {med_info.get('brand_name')}\n"
                f"**Generic Name:** {med_info.get('generic_name')}\n"
                f"**Category:** {med_info.get('category')}\n\n"
                f"**Purpose:** {med_info.get('purpose')}\n"
                f"**Standard Dosage:** {med_info.get('standard_dosage')}\n\n"
                f"**Precautions:**\n" + "\n".join(f"- {p}" for p in med_info.get("precautions", [])) + "\n\n"
                f"**Potential Side Effects:**\n" + "\n".join(f"- {s}" for s in med_info.get("side_effects", [])) + "\n\n"
                f"**Allergy Check:** {allergy_status}"
            )
        else:
            output_text = (
                f"### 💊 Medication Information\n\n"
                f"{med_info.get('message', 'Medicine not found.')}\n\n"
                f"**Allergy Check:** {allergy_status}"
            )

        # Enhance with LLM for patient-friendly explanation
        if self.llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                res = self.llm.invoke([
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(
                        content=(
                            f"Patient Query: {last_user_message}\n"
                            f"Structured Medication Data:\n{output_text}\n\n"
                            "Provide a concise, patient-friendly explanation. "
                            "Do NOT copy the raw data verbatim. Summarize clearly in 3-5 bullet points."
                        )
                    ),
                ])
                if res and res.content:
                    output_text = str(res.content)
            except Exception as e:
                print(f"Medication Agent LLM call fallback: {e}")

        agent_outputs = state.get("agent_outputs", {})
        agent_outputs["medication_info"] = output_text

        return {
            "agent_outputs": agent_outputs,
            "next_node": "reflection_node",
        }


def get_medication_info(state: AgentState) -> Dict[str, Any]:
    agent = MedicationAgent()
    return agent.get_medication_info(state)
