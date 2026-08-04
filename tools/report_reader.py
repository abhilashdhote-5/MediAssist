from typing import Dict, List, Optional
from utils.helpers import load_json_file

REPORTS_DATA_FILE = "data/medical_reports.json"


class ReportReaderTool:
    """
    Tool for reading structured medical reports from data/medical_reports.json
    and PDF lab report files from the file system.
    """

    def _load_reports(self) -> List[Dict]:
        return load_json_file(REPORTS_DATA_FILE, default=[])

    def get_structured_report(self, report_id: str) -> Dict:
        """
        Retrieves a structured lab report by report ID from data/medical_reports.json.
        """
        reports = self._load_reports()
        for report in reports:
            if report.get("report_id", "").upper() == report_id.upper():
                return report
        return {"error": f"Report '{report_id}' not found in database."}

    def get_reports_for_patient(self, patient_id: str) -> List[Dict]:
        """Returns all reports belonging to a specific patient."""
        reports = self._load_reports()
        return [r for r in reports if r.get("patient_id") == patient_id]

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extracts text from a PDF file using pypdf or falls back to plain-text read.
        """
        import os
        if not os.path.exists(pdf_path):
            return f"[Error] PDF file not found at: {pdf_path}"

        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        except Exception as e:
            try:
                with open(pdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception:
                return f"[Error extracting PDF text: {str(e)}]"

    def get_report_with_pdf_text(self, report_id: str) -> Dict:
        """
        Returns structured report data and any available PDF text content.
        """
        report = self.get_structured_report(report_id)
        if "error" in report:
            return report

        pdf_path = report.get("file_path", "")
        pdf_text = ""
        if pdf_path:
            pdf_text = self.extract_text_from_pdf(pdf_path)

        return {
            **report,
            "pdf_text": pdf_text,
        }

    def highlight_abnormalities(self, lab_results: List[Dict]) -> List[Dict]:
        """Returns only abnormal lab results (High or Low status)."""
        return [r for r in lab_results if r.get("status") in ("High", "Low")]