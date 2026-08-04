import os
from typing import List, Dict, Optional
from utils.helpers import load_json_file

DATA_FILE = "data/doctors.json"


class DoctorLookupTool:
    """
    Tool for looking up doctors from the data/doctors.json file.
    Supports search by specialty, name, and doctor ID.
    """

    def _load_doctors(self) -> List[Dict]:
        return load_json_file(DATA_FILE, default=[])

    def search_doctors(self, specialty: str = "", name: str = "") -> List[Dict]:
        """
        Search doctors by specialty and/or name substring.
        Returns all doctors if no filters are provided.
        """
        doctors = self._load_doctors()
        results = []
        for doctor in doctors:
            specialty_match = (
                specialty.lower() in doctor.get("specialty", "").lower()
                if specialty else True
            )
            name_match = (
                name.lower() in doctor.get("full_name", "").lower()
                if name else True
            )
            if specialty_match and name_match:
                results.append(doctor)
        return results

    def get_doctor(self, doctor_id: str = "", name: str = "") -> Dict:
        """
        Get a specific doctor by ID or exact name.
        """
        doctors = self._load_doctors()
        for doctor in doctors:
            if doctor_id and doctor.get("doctor_id", "").upper() == doctor_id.upper():
                return doctor
            if name and name.lower() == doctor.get("full_name", "").lower():
                return doctor
        return {"error": "Doctor not found"}

    def get_all_specialties(self) -> List[str]:
        """Returns a unique sorted list of all specialties available."""
        doctors = self._load_doctors()
        return sorted(set(d.get("specialty", "") for d in doctors if d.get("specialty")))


# ---------------------------------------------------------------------------
# Backward-compatible standalone functions
# ---------------------------------------------------------------------------

def find_doctors(specialty: str) -> List[Dict]:
    return DoctorLookupTool().search_doctors(specialty=specialty)


def get_doctor(name: str) -> Dict:
    return DoctorLookupTool().get_doctor(name=name)