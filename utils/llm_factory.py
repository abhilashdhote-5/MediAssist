import os
from dotenv import load_dotenv

load_dotenv()

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")

def get_groq_api_key(key_index: int = 1) -> str:
    """
    Retrieves specified Groq API key from environment variables.
    """
    if key_index == 1:
        key = os.getenv("GROK_API_KEY_1") or os.getenv("GROQ_API_KEY_1") or ""
    else:
        key = os.getenv("GROK_API_KEY_2") or os.getenv("GROQ_API_KEY_2") or ""
    return key.strip().strip('"').strip("'")

def get_llm_for_task(task_name: str, model_name: str = DEFAULT_GROQ_MODEL):
    """
    Returns an LLM instance assigned to a specific Groq API key to distribute request load.
    
    Load Distribution Strategy:
    - Key 1: 'supervisor', 'appointment', 'medication'
    - Key 2: 'symptom', 'report', 'reflection'
    """
    key_mapping = {
        "supervisor": 1,
        "appointment": 1,
        "medication": 1,
        "symptom": 2,
        "report": 2,
        "reflection": 2
    }
    
    key_index = key_mapping.get(task_name.lower().strip(), 1)
    api_key = get_groq_api_key(key_index)
    
    if not api_key or "your_" in api_key.lower():
        return None

    try:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=api_key,
            base_url=GROQ_BASE_URL,
            model=model_name,
            temperature=0.1
        )
    except Exception as e:
        print(f"Warning: Could not initialize LLM for task '{task_name}': {e}")
        return None
