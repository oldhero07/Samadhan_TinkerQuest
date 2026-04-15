"""
Khet — Crop Advisor Agent
Responds to crop problems in simple Hindi.
Supports optional image input for visual crop diagnosis.
"""
import os
import json
import base64
from pathlib import Path
from google import genai
from google.genai import types

_client = None

SYSTEM_PROMPT = (
    "You are Khet, a crop advisor for Indian farmers. "
    "You speak simple Hindi. You are warm and practical, like a knowledgeable neighbour. "
    "Given a crop problem, respond with: cause, immediate action, and one sentence about "
    "government support if relevant. Keep responses under 4 sentences. "
    "Always respond in Hindi (Devanagari script)."
)

KNOWLEDGE_PATH = Path(__file__).parent.parent / "knowledge" / "crops.json"


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _load_knowledge() -> str:
    try:
        data = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
        lines = ["Known crop problems for reference:"]
        for item in data:
            lines.append(f"- {item['problem']}: {item['solution']}")
        return "\n".join(lines)
    except Exception:
        return ""


def _media_type(b64: str) -> str:
    header = b64[:16]
    if header.startswith("/9j/"):
        return "image/jpeg"
    if header.startswith("iVBOR"):
        return "image/png"
    if header.startswith("UklGR"):
        return "image/webp"
    return "image/jpeg"


def ask_khet(text: str, profile: dict, image_b64=None) -> str:
    """
    Returns a Hindi crop advice response.
    Optionally accepts a base64-encoded image for visual diagnosis.
    """
    client = _get_client()
    knowledge_context = _load_knowledge()

    # Build profile context snippet
    profile_snippet = ""
    if profile:
        parts = []
        if profile.get("location"):
            parts.append(f"स्थान: {profile['location']}")
        if profile.get("crops"):
            parts.append(f"फसलें: {', '.join(profile['crops'])}")
        if parts:
            profile_snippet = "किसान की जानकारी: " + "; ".join(parts) + "\n\n"

    full_text = (
        f"{knowledge_context}\n\n{profile_snippet}किसान का सवाल: {text}"
        if knowledge_context
        else f"{profile_snippet}किसान का सवाल: {text}"
    )

    contents = []
    if image_b64:
        contents.append(types.Part.from_bytes(
            data=base64.b64decode(image_b64),
            mime_type=_media_type(image_b64),
        ))
    contents.append(full_text)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=512,
            ),
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Khet error] {e}")
        return "माफ करें, फसल की जानकारी अभी उपलब्ध नहीं है। कृपया दोबारा कोशिश करें।"
