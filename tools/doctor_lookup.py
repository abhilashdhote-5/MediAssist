from typing import Any, Dict, List, Optional
from utils.helpers import load_json_file

class DoctorLookupTool:
    """
    Tool for querying doctor directory and schedule availability.
    """
    def __init__(self, json_path: str = "data/doctors.json"):
        self.json_path = json_path

    def search_doctors(self, specialty: Optional[str] = None, day: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Searches available doctors matching requested specialty and/or available day.
        """
        doctors = load_json_file(self.json_path, default=[])
        results = []
        for doc in doctors:
            match_specialty = True
            match_day = True

            if specialty:
                match_specialty = specialty.lower() in doc.get("specialty", "").lower()
            if day:
                match_day = any(day.lower() in d.lower() for d in doc.get("available_days", []))

            if match_specialty and match_day:
                results.append(doc)

        return results if results else doctors
