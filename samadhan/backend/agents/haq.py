"""
Haq — Government Scheme Advisor Agent
Checks scheme eligibility and explains in simple Hindi.
"""
import os
import json
from pathlib import Path
from google import genai
from google.genai import types

_client = None

SYSTEM_PROMPT = (
    "You are Haq, a government scheme advisor. You speak simple Hindi. "
    "Given a farmer's profile (crops, location, income level) and a query, "
    "identify which of the following schemes they may be eligible for and explain simply: "
    "PM Fasal Bima Yojana, PM Kisan Samman Nidhi, Kisan Credit Card, "
    "Pradhan Mantri Krishi Sinchayee Yojana, Soil Health Card. "
    "Be direct. No jargon. Always respond in Hindi (Devanagari script)."
)

KNOWLEDGE_PATH = Path(__file__).parent.parent / "knowledge" / "schemes.json"


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _load_knowledge() -> str:
    try:
        data = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
        lines = ["Scheme reference:"]
        for item in data:
            lines.append(
                f"- {item['name']}: {item['benefit']} | पात्रता: {item['eligibility']} | "
                f"कैसे आवेदन करें: {item['how_to_apply']}"
            )
        return "\n".join(lines)
    except Exception:
        return ""


def ask_haq(text: str, profile: dict) -> str:
    """
    Returns Hindi scheme eligibility advice based on farmer's profile.
    """
    client = _get_client()
    knowledge_context = _load_knowledge()

    # Build profile context
    profile_parts = []
    if profile.get("location"):
        profile_parts.append(f"राज्य/जिला: {profile['location']}")
    if profile.get("crops"):
        profile_parts.append(f"फसलें: {', '.join(profile['crops'])}")
    if profile.get("land_acres"):
        profile_parts.append(f"जमीन: {profile['land_acres']} एकड़")
    if profile.get("income_level"):
        profile_parts.append(f"आय वर्ग: {profile['income_level']}")

    profile_text = (
        "किसान की जानकारी:\n" + "\n".join(f"  - {p}" for p in profile_parts)
        if profile_parts
        else "किसान की पूरी जानकारी उपलब्ध नहीं है।"
    )

    user_text = (
        f"{knowledge_context}\n\n{profile_text}\n\nसवाल: {text}"
        if knowledge_context
        else f"{profile_text}\n\nसवाल: {text}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=512,
            ),
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Haq error] {e}")
        return "माफ करें, योजना की जानकारी अभी उपलब्ध नहीं है। कृपया दोबारा कोशिश करें।"
