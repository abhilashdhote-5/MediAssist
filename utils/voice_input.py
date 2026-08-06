"""
Voice Input Utility — Groq Whisper STT
Reads the VOICE API key from .env and transcribes audio bytes using
the groq Python client with the whisper-large-v3-turbo model.
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> Optional[str]:
    """
    Transcribes audio bytes to text using Groq's Whisper API.

    Args:
        audio_bytes: Raw audio file bytes (webm, wav, mp3, m4a, ogg supported).
        filename: Hint for the file format (affects MIME detection).

    Returns:
        Transcribed text string, or None on failure.
    """
    api_key = os.getenv("VOICE", "").strip()
    if not api_key:
        print("[VoiceInput] VOICE API key not found in .env")
        return None

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        # Groq expects a file-like object with a name attribute
        import io
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename  # type: ignore[attr-defined]

        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=audio_file,
            response_format="text",
        )

        # response_format="text" returns a plain string
        if isinstance(transcription, str):
            return transcription.strip()
        # Fallback for object response
        return str(getattr(transcription, "text", transcription)).strip()

    except Exception as e:
        print(f"[VoiceInput] Transcription error: {e}")
        return None
