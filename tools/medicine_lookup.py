from typing import Dict, List, Optional
from utils.helpers import load_json_file

DATA_FILE = "data/medicines.json"


class MedicineLookupTool:
    """
    Tool for looking up medicine information from data/medicines.json.
    Supports search by brand name, generic name, category, or medicine ID.
    """

    def _load_medicines(self) -> List[Dict]:
        return load_json_file(DATA_FILE, default=[])

    def query_medicine(self, query: str) -> Dict:
        """
        Search for a medicine by brand name, generic name, category, or medicine ID.
        Returns structured medicine info or a 'not found' message.
        """
        medicines = self._load_medicines()
        query_lower = query.lower().strip()

        for med in medicines:
            brand = med.get("brand_name", "").lower()
            generic = med.get("generic_name", "").lower()
            category = med.get("category", "").lower()
            med_id = med.get("medicine_id", "").lower()

            if (
                query_lower in brand
                or query_lower in generic
                or any(word in brand for word in query_lower.split())
                or any(word in generic for word in query_lower.split())
                or query_lower in med_id
                or query_lower in category
            ):
                return {
                    "medicine_id": med.get("medicine_id"),
                    "brand_name": med.get("brand_name"),
                    "generic_name": med.get("generic_name"),
                    "category": med.get("category"),
                    "purpose": med.get("purpose"),
                    "standard_dosage": med.get("standard_dosage"),
                    "precautions": med.get("precautions", []),
                    "side_effects": med.get("side_effects", []),
                    "important_note": (
                        "This information is for general education only and does not "
                        "replace professional medical advice. Always follow your doctor's guidance."
                    ),
                }

        return {
            "message": (
                f"No medicine found matching '{query}'. "
                "Please consult your doctor or pharmacist for specific medication queries."
            )
        }

    def search_by_category(self, category: str) -> List[Dict]:
        """Returns all medicines in a given category."""
        medicines = self._load_medicines()
        return [
            m for m in medicines
            if category.lower() in m.get("category", "").lower()
        ]

    def list_all_medicines(self) -> List[Dict]:
        """Returns all medicines in the database."""
        return self._load_medicines()


# ---------------------------------------------------------------------------
# Backward-compatible standalone function
# ---------------------------------------------------------------------------

def lookup_medicine(name: str) -> Dict:
    return MedicineLookupTool().query_medicine(name)