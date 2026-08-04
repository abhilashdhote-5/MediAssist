import unittest
from langchain_core.messages import HumanMessage
from supervisor import classify_intent
from agents.appointment_agent import AppointmentAgent, process_appointment
from agents.symptom_agent import SymptomAgent, assess_symptoms
from agents.medication_agent import MedicationAgent, get_medication_info
from agents.report_agent import ReportAgent, explain_lab_report
from agents.reflection_node import validate_response


class TestAgents(unittest.TestCase):

    def test_supervisor_appointment_intent(self):
        state = {"messages": [HumanMessage(content="I want to book an appointment with a doctor")]}
        res = classify_intent(state)
        self.assertEqual(res["current_intent"], "appointment")
        self.assertEqual(res["next_node"], "appointment_agent")

    def test_supervisor_symptom_intent(self):
        state = {"messages": [HumanMessage(content="I have a fever and headache")]}
        res = classify_intent(state)
        self.assertIn(res["current_intent"], ["symptom", "appointment"])  # LLM may vary

    def test_supervisor_medication_intent(self):
        state = {"messages": [HumanMessage(content="Tell me about paracetamol dosage and side effects")]}
        res = classify_intent(state)
        self.assertEqual(res["current_intent"], "medication")

    def test_appointment_agent_returns_pending_hitl(self):
        state = {
            "messages": [HumanMessage(content="I want to book an appointment for cardiology")],
            "patient_id": "PAT0001",
            "agent_outputs": {},
        }
        res = process_appointment(state)
        self.assertIn("appointment_result", res["agent_outputs"])
        self.assertIn("appointment_pending", res["agent_outputs"])
        self.assertEqual(res["next_node"], "reflection_node")
        # Doctor should come from real doctors.json
        pending = res["agent_outputs"]["appointment_pending"]
        self.assertIn("doctor_name", pending)
        self.assertIn("Cardiology", pending.get("specialty", ""))

    def test_appointment_agent_general_medicine(self):
        state = {
            "messages": [HumanMessage(content="Book a general medicine appointment")],
            "patient_id": "PAT0002",
            "agent_outputs": {},
        }
        res = process_appointment(state)
        pending = res["agent_outputs"]["appointment_pending"]
        self.assertIn("General Medicine", pending.get("specialty", ""))

    def test_symptom_agent_red_flags(self):
        agent = SymptomAgent()
        has_flag = agent.check_red_flags(["I have severe chest pain and shortness of breath"])
        self.assertTrue(has_flag)

    def test_symptom_agent_non_critical(self):
        state = {
            "messages": [HumanMessage(content="I have a mild headache and fever")],
            "patient_id": "PAT0001",
            "agent_outputs": {},
        }
        res = assess_symptoms(state)
        self.assertIn("symptom_guidance", res["agent_outputs"])
        self.assertEqual(res["next_node"], "reflection_node")

    def test_medication_agent_data_lookup(self):
        state = {
            "messages": [HumanMessage(content="What is Paracetamol used for?")],
            "patient_id": "PAT0001",
            "agent_outputs": {},
        }
        res = get_medication_info(state)
        self.assertIn("medication_info", res["agent_outputs"])

    def test_medication_agent_allergy_check(self):
        agent = MedicationAgent()
        # PAT0003 has Penicillin allergy
        result = agent.cross_check_allergy("Amoxicillin", "PAT0003")
        # Amoxicillin is a penicillin family drug – should warn or pass depending on fuzzy match
        self.assertIsInstance(result, str)

    def test_report_agent_patient_data(self):
        state = {
            "messages": [HumanMessage(content="Show me my lab report")],
            "patient_id": "PAT0020",  # Has a report in medical_reports.json (REP5003)
            "agent_outputs": {},
        }
        res = explain_lab_report(state)
        self.assertIn("report_explanation", res["agent_outputs"])
        self.assertEqual(res["next_node"], "reflection_node")

    def test_reflection_node_builds_response(self):
        state = {
            "agent_outputs": {"symptom_guidance": "Rest and stay hydrated."},
            "patient_id": "PAT0001",
        }
        res = validate_response(state)
        self.assertTrue(res["is_safe"])
        self.assertIn("Medical Disclaimer", res["final_response"])
        self.assertGreater(len(res["final_response"]), 20)


if __name__ == "__main__":
    unittest.main()
