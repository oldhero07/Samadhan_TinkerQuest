"""
Sunno — Router / Orchestrator Agent
Classifies a Hindi farmer query into one of:
  CROP_PROBLEM | SCHEME_QUERY | GENERAL
"""
import os
from google import genai
from google.genai import types

_client = None

SYSTEM_PROMPT = (
    "You are Sunno, a routing assistant. "
    "Given a Hindi farmer query, classify it as one of: CROP_PROBLEM, SCHEME_QUERY, GENERAL. "
    "Return only the category label. Nothing else."
)

VALID_INTENTS = {"CROP_PROBLEM", "SCHEME_QUERY", "GENERAL"}


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def route_query(text: str) -> str:
    """
    Returns one of: CROP_PROBLEM, SCHEME_QUERY, GENERAL.
    Falls back to GENERAL on any API error.
    """
    try:
        client = _get_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=64,
            ),
        )
        intent = response.text.strip().upper()
        if intent not in VALID_INTENTS:
            return "GENERAL"
        return intent
    except Exception as e:
        print(f"[Sunno error] {e}")
        return "GENERAL"
