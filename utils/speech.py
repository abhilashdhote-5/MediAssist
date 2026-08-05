# utils/speech.py
import io
import os
from groq import Groq

def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """
    Transcribes raw audio bytes from Streamlit audio recorder using Groq Whisper.
    """
    api_key = os.getenv("GROK_API_KEY_1") or os.getenv("GROQ_API_KEY_1") or ""
    if not api_key:
        return ""
    
    try:
        client = Groq(api_key=api_key)
        
        # Pass audio bytes in tuple format expected by Groq client (filename, bytes, content_type)
        audio_file = ("user_voice.wav", audio_bytes, "audio/wav")
        
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            response_format="text",
            language="en"
        )
        return str(transcription).strip()
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""