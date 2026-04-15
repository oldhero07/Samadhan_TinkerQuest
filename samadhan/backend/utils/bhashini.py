"""
Bhashini STT/TTS wrapper.
Bhashini is India's AI-based language translation platform (bhashini.gov.in).
This module wraps the Bhashini ULCA (Unified Language Contribution API).

Environment variables required:
  BHASHINI_USER_ID
  BHASHINI_API_KEY
  BHASHINI_PIPELINE_ID

Reference:
  https://bhashini.gitbook.io/bhashini-apis/
"""
import os
import base64
import requests

BHASHINI_INFERENCE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

# Language codes
HINDI = "hi"
SOURCE_SCRIPT = "Deva"


def _headers() -> dict:
    return {
        "userID": os.getenv("BHASHINI_USER_ID", ""),
        "ulcaApiKey": os.getenv("BHASHINI_API_KEY", ""),
        "Content-Type": "application/json",
    }


def _to_wav_base64(audio_bytes: bytes) -> str:
    """
    Convert any audio format (WebM, MP3, OGG…) to 16kHz mono WAV base64.
    Bhashini ASR requires 16kHz mono WAV.
    Requires ffmpeg installed: brew install ffmpeg / apt install ffmpeg.
    Falls back to sending raw bytes if pydub/ffmpeg not available.
    """
    try:
        import io
        from pydub import AudioSegment
        seg = AudioSegment.from_file(io.BytesIO(audio_bytes))
        seg = seg.set_frame_rate(16000).set_channels(1)
        buf = io.BytesIO()
        seg.export(buf, format="wav")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"[Audio conversion warning] {e} — sending raw bytes")
        return base64.b64encode(audio_bytes).decode("utf-8")


def stt(audio_bytes: bytes, language: str = HINDI) -> str:
    """
    Speech-to-Text: converts audio bytes to Hindi text.
    Returns empty string on failure.

    audio_bytes: raw audio in any format (WebM from browser, WAV, MP3…)
                 automatically converted to 16kHz mono WAV before sending.
    """
    pipeline_id = os.getenv("BHASHINI_PIPELINE_ID", "")
    if not pipeline_id:
        # Dev fallback: return placeholder so the rest of the flow can be tested
        return "[STT not configured — set BHASHINI_PIPELINE_ID]"

    audio_b64 = _to_wav_base64(audio_bytes)

    payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": language},
                    "serviceId": "",
                    "audioFormat": "wav",
                    "samplingRate": 16000,
                },
            }
        ],
        "inputData": {
            "audio": [{"audioContent": audio_b64}]
        },
    }

    try:
        resp = requests.post(
            BHASHINI_INFERENCE_URL,
            json=payload,
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        output = data["pipelineResponse"][0]["output"][0]["source"]
        return output.strip()
    except Exception as e:
        print(f"[Bhashini STT error] {e}")
        return ""


def tts(text: str, language: str = HINDI):
    """
    Text-to-Speech: converts Hindi text to audio bytes (MP3).
    Returns None on failure.
    """
    pipeline_id = os.getenv("BHASHINI_PIPELINE_ID", "")
    if not pipeline_id:
        return None

    payload = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {"sourceLanguage": language},
                    "serviceId": "",
                    "gender": "female",
                    "samplingRate": 8000,
                },
            }
        ],
        "inputData": {
            "input": [{"source": text}]
        },
    }

    try:
        resp = requests.post(
            BHASHINI_INFERENCE_URL,
            json=payload,
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        audio_b64 = data["pipelineResponse"][0]["audio"][0]["audioContent"]
        return base64.b64decode(audio_b64)
    except Exception as e:
        print(f"[Bhashini TTS error] {e}")
        return None
