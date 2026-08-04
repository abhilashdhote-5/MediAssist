import unittest
from tools.doctor_lookup import DoctorLookupTool
from tools.appointment_tool import AppointmentTool
from tools.medicine_lookup import MedicineLookupTool
from tools.report_reader import ReportReaderTool


class TestTools(unittest.TestCase):

    def test_doctor_lookup_by_specialty(self):
        tool = DoctorLookupTool()
        docs = tool.search_doctors(specialty="General Medicine")
        self.assertTrue(len(docs) > 0, "Should find General Medicine doctors")
        for d in docs:
            self.assertIn("General Medicine", d.get("specialty", ""))

    def test_doctor_lookup_all(self):
        tool = DoctorLookupTool()
        docs = tool.search_doctors()
        self.assertTrue(len(docs) > 0, "Should return all doctors when no filter")

    def test_doctor_get_by_id(self):
        tool = DoctorLookupTool()
        doctor = tool.get_doctor(doctor_id="DOC001")
        self.assertIn("doctor_id", doctor, "Should find doctor by ID")
        self.assertEqual(doctor["doctor_id"], "DOC001")

    def test_appointment_booking(self):
        tool = AppointmentTool()
        res = tool.book_appointment(
            patient_id="PAT0001",
            doctor_id="DOC001",
            date="2026-09-01",
            time_slot="10:00 AM",
            reason="Unit test appointment",
            patient_name="Test Patient",
            doctor_name="Dr. Test Doctor",
        )
        self.assertEqual(res["status"], "Success")
        self.assertIn("appointment", res)
        appt = res["appointment"]
        self.assertTrue(appt["appointment_id"].startswith("APT"))

    def test_appointment_cancel(self):
        tool = AppointmentTool()
        # Book first, then cancel
        book_res = tool.book_appointment(
            patient_id="PAT_TEST_CANCEL",
            doctor_id="DOC001",
            date="2026-09-05",
            time_slot="09:00 AM",
            reason="Test cancel",
        )
        appt_id = book_res["appointment"]["appointment_id"]
        cancel_res = tool.cancel_appointment(appt_id)
        self.assertEqual(cancel_res["status"], "Success")
        self.assertEqual(cancel_res["appointment"]["status"], "Cancelled")

    def test_appointment_list_by_patient(self):
        tool = AppointmentTool()
        appts = tool.list_appointments(patient_id="PAT8801")
        for a in appts:
            self.assertEqual(a["patient_id"], "PAT8801")

    def test_medicine_lookup_paracetamol(self):
        tool = MedicineLookupTool()
        res = tool.query_medicine("Paracetamol")
        self.assertIn("generic_name", res, "Should find Paracetamol")
        self.assertEqual(res.get("generic_name"), "Acetaminophen")

    def test_medicine_lookup_ibuprofen(self):
        tool = MedicineLookupTool()
        res = tool.query_medicine("ibuprofen")
        self.assertIn("brand_name", res, "Should find Ibuprofen")

    def test_medicine_lookup_not_found(self):
        tool = MedicineLookupTool()
        res = tool.query_medicine("NONEXISTENT_DRUG_XYZ123")
        self.assertIn("message", res, "Should return not-found message")

    def test_report_reader_by_id(self):
        tool = ReportReaderTool()
        rep = tool.get_structured_report("REP5001")
        self.assertEqual(rep.get("report_id"), "REP5001")
        self.assertTrue(len(rep.get("lab_results", [])) > 0)

    def test_report_reader_not_found(self):
        tool = ReportReaderTool()
        rep = tool.get_structured_report("REPXXXX")
        self.assertIn("error", rep)

    def test_report_abnormalities(self):
        tool = ReportReaderTool()
        lab_results = [
            {"parameter": "Cholesterol", "value": 220, "unit": "mg/dL", "status": "High"},
            {"parameter": "Hemoglobin", "value": 13.5, "unit": "g/dL", "status": "Normal"},
        ]
        abnormal = tool.highlight_abnormalities(lab_results)
        self.assertEqual(len(abnormal), 1)
        self.assertEqual(abnormal[0]["parameter"], "Cholesterol")


if __name__ == "__main__":
    unittest.main()
