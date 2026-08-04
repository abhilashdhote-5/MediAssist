import unittest
from langchain_core.messages import HumanMessage
from supervisor import classify_intent
from agents.appointment_agent import process_appointment
from agents.symptom_agent import assess_symptoms, SymptomAgent
from agents.medication_agent import get_medication_info, MedicationAgent
from agents.report_agent import explain_lab_report
from agents.reflection_node import validate_response

class TestAgents(unittest.TestCase):
    def test_supervisor_intent_classification(self):
        state = {"messages": [HumanMessage(content="I want to book an appointment with a doctor")]}
        res = classify_intent(state)
        self.assertEqual(res["current_intent"], "appointment")
        self.assertEqual(res["next_node"], "appointment_agent")

    def test_appointment_agent(self):
        state = {
            "messages": [HumanMessage(content="Book an appointment for Dr. Sarah Jenkins")],
            "patient_id": "PAT8801",
            "agent_outputs": {}
        }
        res = process_appointment(state)
        self.assertIn("appointment_result", res["agent_outputs"])
        self.assertEqual(res["next_node"], "reflection_node")

    def test_symptom_agent_red_flags(self):
        agent = SymptomAgent()
        has_red_flag = agent.check_red_flags(["severe chest pain and shortness of breath"])
        self.assertTrue(has_red_flag)

    def test_medication_allergy_check(self):
        agent = MedicationAgent()
        allergy_msg = agent.cross_check_allergy("Penicillin", "PAT8801")
        self.assertIn("ALLERGY WARNING", allergy_msg)

    def test_reflection_node(self):
        state = {
            "agent_outputs": {"symptom_guidance": "Rest and drink water."},
            "patient_id": "PAT8801"
        }
        res = validate_response(state)
        self.assertTrue(res["is_safe"])
        self.assertIn("Medical Disclaimer", res["final_response"])

if __name__ == "__main__":
    unittest.main()
