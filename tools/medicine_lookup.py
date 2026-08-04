from typing import Dict

MEDICINES = {
    "paracetamol": {
        "use": "Relief from fever and mild to moderate pain",
        "usual_dosage": "As prescribed by a healthcare professional",
        "precautions": "Avoid exceeding the recommended daily dose",
        "side_effects": "Nausea, rash, or liver problems in case of overdose"
    },
    "ibuprofen": {
        "use": "Pain, inflammation, and fever relief",
        "usual_dosage": "Take with food if advised by your doctor",
        "precautions": "Use carefully in patients with stomach ulcers or kidney disease",
        "side_effects": "Stomach upset, dizziness, or heartburn"
    }
}


def lookup_medicine(name: str) -> Dict:
    medicine = MEDICINES.get(name.lower())

    if not medicine:
        return {
            "error": "Medicine not found in database"
        }

    return {
        "medicine": name.title(),
        **medicine,
        "important_note": "This information is for general education only and does not replace medical advice."
    }