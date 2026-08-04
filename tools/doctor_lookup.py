from typing import List, Dict

DOCTORS = [
    {
        "name": "Dr. Priya Sharma",
        "specialty": "Cardiology",
        "available_slots": ["10:00 AM", "2:00 PM"]
    },
    {
        "name": "Dr. Rahul Mehta",
        "specialty": "General Medicine",
        "available_slots": ["11:00 AM", "4:00 PM"]
    },
    {
        "name": "Dr. Anjali Desai",
        "specialty": "Dermatology",
        "available_slots": ["9:30 AM", "1:30 PM"]
    }
]


def find_doctors(specialty: str) -> List[Dict]:
    return [
        doctor for doctor in DOCTORS
        if specialty.lower() in doctor["specialty"].lower()
    ]


def get_doctor(name: str) -> Dict:
    for doctor in DOCTORS:
        if name.lower() == doctor["name"].lower():
            return doctor
    return {"error": "Doctor not found"}