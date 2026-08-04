from langchain.tools import tool

from .appointment_tool import book_appointment
from .doctor_lookup import find_doctors
from .medicine_lookup import lookup_medicine


@tool
def appointment_scheduler(patient_name: str, doctor: str, date: str, time: str):
    """Book a patient appointment."""
    return book_appointment(patient_name, doctor, date, time)


@tool
def doctor_lookup(specialty: str):
    """Find doctors by specialty."""
    return find_doctors(specialty)


@tool
def medicine_database(medicine_name: str):
    """Get medicine information and precautions."""
    return lookup_medicine(medicine_name)