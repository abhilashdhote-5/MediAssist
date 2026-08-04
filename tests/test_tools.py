import unittest
from tools.doctor_lookup import DoctorLookupTool
from tools.appointment_tool import AppointmentTool
from tools.medicine_lookup import MedicineLookupTool
from tools.report_reader import ReportReaderTool

class TestTools(unittest.TestCase):
    def test_doctor_lookup(self):
        tool = DoctorLookupTool()
        docs = tool.search_doctors(specialty="General Medicine")
        self.assertTrue(len(docs) > 0)
        self.assertEqual(docs[0]["specialty"], "General Medicine")

    def test_appointment_booking(self):
        tool = AppointmentTool()
        res = tool.book_appointment("PAT8801", "DOC001", "2026-08-15", "09:00 AM", "Test visit")
        self.assertEqual(res["status"], "Success")
        self.assertIn("appointment", res)

    def test_medicine_lookup(self):
        tool = MedicineLookupTool()
        res = tool.query_medicine("Paracetamol")
        self.assertEqual(res.get("generic_name"), "Acetaminophen")

    def test_report_reader(self):
        tool = ReportReaderTool()
        rep = tool.get_structured_report("REP5001")
        self.assertEqual(rep.get("report_id"), "REP5001")
        self.assertTrue(len(rep.get("lab_results", [])) > 0)

if __name__ == "__main__":
    unittest.main()
