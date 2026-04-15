"""
Groq Whisper Large V3 — Hindi Speech-to-Text.
Free tier, sub-second inference, excellent Hindi accent handling.

Falls back gracefully if GROQ_API_KEY is not configured.
"""
import os
import tempfile

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return None
        try:
            from groq import Groq
            _client = Groq(api_key=api_key)
        except Exception as e:
            print(f"[Groq init error] {e}")
            return None
    return _client


def transcribe(audio_bytes: bytes, language: str = "hi") -> str:
    """
    Transcribe audio bytes to Hindi text using Groq Whisper Large V3.
    Returns empty string on failure or if not configured.

    audio_bytes: raw audio in any format (WebM from browser, WAV, MP3)
    """
    client = _get_client()
    if client is None:
        print("[Groq STT] Not configured — set GROQ_API_KEY")
        return ""

    # Write audio to a temp file (Groq API needs a file-like object)
    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                language=language,
                response_format="text",
            )

        os.unlink(tmp_path)
        result = transcription.strip() if isinstance(transcription, str) else str(transcription).strip()
        print(f"[Groq STT] Transcribed: {result[:80]}...")
        return result

    except Exception as e:
        print(f"[Groq STT error] {e}")
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        return ""
