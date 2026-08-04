from typing import Any, Dict, Optional
from utils.helpers import load_json_file

class MedicineLookupTool:
    """
    Tool for retrieving medicine information, usage, precautions, and side effects.
    """
    def __init__(self, json_path: str = "data/medicines.json"):
        self.json_path = json_path

    def query_medicine(self, medicine_name: str) -> Dict[str, Any]:
        """
        Fuzzy matches medicine name against medicines.json database.
        """
        medicines = load_json_file(self.json_path, default=[])
        query_lower = medicine_name.lower().strip()
        
        for med in medicines:
            if (query_lower in med.get("brand_name", "").lower() or
                query_lower in med.get("generic_name", "").lower() or
                query_lower in med.get("category", "").lower()):
                return med
                
        return {
            "status": "Not Found",
            "message": f"No detailed entry found for medicine '{medicine_name}'. Please consult a registered pharmacist or physician."
        }
