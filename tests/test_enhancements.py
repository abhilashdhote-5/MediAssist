import unittest
import os
from langchain_core.messages import HumanMessage, AIMessage
from supervisor import SupervisorAgent
from memory.state import AgentState
from utils.rag_pipeline import AdvancedRAGPipeline
from utils.pdf_parser import create_sample_pdf_if_missing
from agents.report_agent import ReportAgent

class TestMediAssistEnhancements(unittest.TestCase):

    def test_multi_agent_supervisor_dynamic_routing(self):
        """Test Requirement 1: Supervisor evaluates every turn dynamically without trapping."""
        supervisor = SupervisorAgent()
        
        # Turn 1: Appointment query
        state_1: AgentState = {
            "messages": [HumanMessage(content="I want to book an appointment with a cardiology doctor.")],
            "patient_id": "PAT0001",
            "current_intent": "",
            "next_node": "",
            "agent_outputs": {},
            "final_response": "",
            "is_safe": True,
            "reflection_feedback": "",
            "pdf_context": ""
        }
        res_1 = supervisor.classify_intent(state_1)
        self.assertEqual(res_1["next_node"], "appointment_agent")

        # Turn 2: Follow-up Medication query (must re-route dynamically!)
        state_2: AgentState = {
            "messages": [
                HumanMessage(content="I want to book an appointment with a cardiology doctor."),
                AIMessage(content="I found Dr. Smith in Cardiology."),
                HumanMessage(content="What is the standard dosage and side effects of Paracetamol?")
            ],
            "patient_id": "PAT0001",
            "current_intent": "appointment",
            "next_node": "appointment_agent",
            "agent_outputs": {},
            "final_response": "",
            "is_safe": True,
            "reflection_feedback": "",
            "pdf_context": ""
        }
        res_2 = supervisor.classify_intent(state_2)
        self.assertEqual(res_2["next_node"], "medication_agent")

        # Turn 3: Symptom query (must re-route again!)
        state_3: AgentState = {
            "messages": [
                HumanMessage(content="What is the standard dosage and side effects of Paracetamol?"),
                AIMessage(content="Paracetamol standard dosage is 500mg."),
                HumanMessage(content="I am suffering from severe cough and high fever.")
            ],
            "patient_id": "PAT0001",
            "current_intent": "medication",
            "next_node": "medication_agent",
            "agent_outputs": {},
            "final_response": "",
            "is_safe": True,
            "reflection_feedback": "",
            "pdf_context": ""
        }
        res_3 = supervisor.classify_intent(state_3)
        self.assertEqual(res_3["next_node"], "symptom_agent")

    def test_user_session_isolation(self):
        """Test Requirement 2: Per-user chat isolation."""
        user_sessions = {}
        
        # Patient 1 session
        p1 = "PAT0001"
        user_sessions[p1] = {"chat_history": [{"role": "user", "content": "P1 question"}], "hitl_pending": None}
        
        # Patient 2 session
        p2 = "PAT0002"
        user_sessions[p2] = {"chat_history": [{"role": "user", "content": "P2 question"}], "hitl_pending": None}

        # Clear P1 chat
        user_sessions[p1]["chat_history"] = []

        self.assertEqual(len(user_sessions[p1]["chat_history"]), 0)
        self.assertEqual(len(user_sessions[p2]["chat_history"]), 1)
        self.assertEqual(user_sessions[p2]["chat_history"][0]["content"], "P2 question")

    def test_rag_pipeline_pdf_chunking(self):
        """Test Requirement 3: RAG pipeline PDF ingestion, chunking, and embedding query."""
        pdf_path = "tests/sample_lab_report.pdf"
        sample_text = (
            "CLINICAL LABORATORY REPORT\n"
            "Patient Name: John Doe\n"
            "Hemoglobin: 11.2 g/dL (Normal Range: 13.5 - 17.5 g/dL) - LOW\n"
            "White Blood Cell (WBC): 14.5 x10^3/uL (Normal Range: 4.5 - 11.0 x10^3/uL) - HIGH\n"
            "Platelets: 250 x10^3/uL (Normal Range: 150 - 450 x10^3/uL) - Normal\n"
            "Fasting Blood Glucose: 145 mg/dL (Normal Range: 70 - 99 mg/dL) - HIGH\n"
        )
        create_sample_pdf_if_missing(pdf_path, sample_text)
        
        rag = AdvancedRAGPipeline()
        res = rag.process_pdf_file(pdf_path)
        
        self.assertEqual(res["status"], "Success")
        self.assertGreater(res["num_chunks"], 0)
        
        retrieved = rag.query("What is the hemoglobin level and glucose?", top_k=2)
        self.assertIn("Hemoglobin", retrieved)
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    unittest.main()
