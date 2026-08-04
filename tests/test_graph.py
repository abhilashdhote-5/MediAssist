import unittest
from langchain_core.messages import HumanMessage
from graph import build_mediassist_graph

class TestLangGraphWorkflow(unittest.TestCase):
    def setUp(self):
        self.app = build_mediassist_graph()

    def test_full_workflow_symptom_query(self):
        initial_state = {
            "messages": [HumanMessage(content="I have had a fever and cold for two days")],
            "patient_id": "PAT8801",
            "current_intent": "",
            "next_node": "",
            "agent_outputs": {},
            "final_response": "",
            "is_safe": True,
            "reflection_feedback": ""
        }
        final_state = self.app.invoke(initial_state)
        self.assertTrue(len(final_state["final_response"]) > 0)
        self.assertIn("Medical Disclaimer", final_state["final_response"])

    def test_full_workflow_appointment_query(self):
        initial_state = {
            "messages": [HumanMessage(content="I want to book an appointment")],
            "patient_id": "PAT8801",
            "current_intent": "",
            "next_node": "",
            "agent_outputs": {},
            "final_response": "",
            "is_safe": True,
            "reflection_feedback": ""
        }
        final_state = self.app.invoke(initial_state)
        self.assertIn("Appointment", final_state["final_response"])

if __name__ == "__main__":
    unittest.main()
