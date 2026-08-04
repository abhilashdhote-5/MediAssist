import json
import os
from typing import Any, Dict, List

def load_json_file(file_path: str, default: Any = None) -> Any:
    """
    Safely loads JSON content from a specified file path.
    """
    if not os.path.exists(file_path):
        return default if default is not None else []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON from {file_path}: {e}")
        return default if default is not None else []

def save_json_file(file_path: str, data: Any) -> bool:
    """
    Safely saves data into a JSON file path.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error writing JSON to {file_path}: {e}")
        return False

def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Formats numeric amount with currency symbol.
    """
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}
    symbol = symbols.get(currency.upper(), "$")
    return f"{symbol}{amount:.2f}"
