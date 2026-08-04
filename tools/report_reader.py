from typing import Any, Dict, Optional
from utils.helpers import load_json_file
from utils.pdf_parser import extract_pdf_text

class ReportReaderTool:
    """
    Tool for extracting text from PDF reports and fetching structured lab report JSON data.
    """
    def __init__(self, reports_dir: str = "data/sample_reports", json_path: str = "data/medical_reports.json"):
        self.reports_dir = reports_dir
        self.json_path = json_path

    def extract_text_from_pdf(self, pdf_file_path: str) -> str:
        """
        Extracts raw text content from a laboratory report PDF file.
        """
        return extract_pdf_text(pdf_file_path)

    def get_structured_report(self, report_id: str) -> Dict[str, Any]:
        """
        Queries medical_reports.json for pre-parsed laboratory parameters and reference ranges.
        """
        reports = load_json_file(self.json_path, default=[])
        for rep in reports:
            if rep.get("report_id") == report_id:
                return rep
        
        # Return fallback default first report if report_id matches or default requested
        if reports:
            return reports[0]
            
        return {
            "status": "Not Found",
            "message": f"Medical report '{report_id}' not found."
        }
