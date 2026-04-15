from __future__ import annotations
"""
Gemini Engine — Single-call LLM architecture.
Replaces the old Sunno/Khet/Haq multi-agent setup.

One Gemini 2.5 Flash call handles:
  - Conversational Hindi response
  - Domain classification (agriculture/health/schemes)
  - Structured profile update extraction
  - Multi-topic handling
  - Image analysis for crop diagnosis
"""
import os
import json
import re
import base64
from pathlib import Path
from google import genai
from google.genai import types

_client = None

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _load_json(filename: str) -> list | dict:
    path = KNOWLEDGE_DIR / filename
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _build_knowledge_context() -> str:
    """Build the verified knowledge section for the system prompt."""
    sections = []

    # Agriculture knowledge
    crops = _load_json("crops.json")
    if crops:
        lines = ["=== VERIFIED AGRICULTURE KNOWLEDGE (Tier 1) ==="]
        for item in crops:
            lines.append(f"\nCrop: {item.get('crop', item.get('problem', 'Unknown'))}")
            if item.get('problem'):
                lines.append(f"Problem: {item['problem']}")
            if item.get('local_names'):
                lines.append(f"Local names: {', '.join(item['local_names'])}")
            if item.get('symptoms'):
                lines.append(f"Symptoms: {item['symptoms']}")
            if item.get('cause'):
                lines.append(f"Cause: {item['cause']}")
            if item.get('solution') or item.get('treatment'):
                lines.append(f"Treatment: {item.get('treatment', item.get('solution', ''))}")
            if item.get('prevention'):
                lines.append(f"Prevention: {item['prevention']}")
            if item.get('escalation'):
                lines.append(f"Escalation: {item['escalation']}")
        sections.append("\n".join(lines))

    # Schemes knowledge
    schemes = _load_json("schemes.json")
    if schemes:
        lines = ["=== VERIFIED GOVERNMENT SCHEMES KNOWLEDGE (Tier 1) ==="]
        for s in schemes:
            lines.append(f"\nScheme: {s.get('name', s.get('scheme', 'Unknown'))}")
            if s.get('full_name'):
                lines.append(f"Full name: {s['full_name']}")
            if s.get('benefit'):
                lines.append(f"Benefit: {s['benefit']}")
            if s.get('eligibility'):
                lines.append(f"Eligibility: {s['eligibility']}")
            if s.get('documents_needed'):
                docs = s['documents_needed']
                if isinstance(docs, list):
                    docs = ", ".join(docs)
                lines.append(f"Documents needed: {docs}")
            if s.get('how_to_apply'):
                lines.append(f"How to apply: {s['how_to_apply']}")
            if s.get('helpline'):
                lines.append(f"Helpline: {s['helpline']}")
            if s.get('key_dates'):
                lines.append(f"Key dates: {s['key_dates']}")
        sections.append("\n".join(lines))

    # Health triage
    health = _load_json("health.json")
    if health:
        lines = ["=== HEALTH TRIAGE SCENARIOS (Tier 1) ===",
                 "IMPORTANT: NEVER diagnose. NEVER prescribe specific medicines (except basic Paracetamol/ORS). Only triage and refer."]
        for h in health:
            lines.append(f"\nScenario: {h.get('scenario', 'Unknown')}")
            if h.get('symptoms_described'):
                syms = h['symptoms_described']
                if isinstance(syms, list):
                    syms = ", ".join(syms)
                lines.append(f"Keywords: {syms}")
            if h.get('immediate_advice'):
                lines.append(f"Immediate advice: {h['immediate_advice']}")
            if h.get('seek_help_when'):
                lines.append(f"Seek help when: {h['seek_help_when']}")
            if h.get('where_to_go'):
                lines.append(f"Where to go: {h['where_to_go']}")
            if h.get('emergency_signs'):
                signs = h['emergency_signs']
                if isinstance(signs, list):
                    signs = ", ".join(signs)
                lines.append(f"EMERGENCY signs: {signs}")
        sections.append("\n".join(lines))

    # Referral map
    referrals = _load_json("referrals.json")
    if referrals:
        lines = ["=== REFERRAL MAP (Roorkee-Haridwar Region) ==="]
        for r in referrals:
            entry = f"- {r.get('name', 'Unknown')}"
            if r.get('type'):
                entry += f" ({r['type']})"
            if r.get('address'):
                entry += f" — {r['address']}"
            if r.get('phone'):
                entry += f" | Phone: {r['phone']}"
            if r.get('hours'):
                entry += f" | Hours: {r['hours']}"
            lines.append(entry)
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def _build_system_prompt(farmer_context: str = "") -> str:
    """Build the complete system prompt with all sections."""
    knowledge = _build_knowledge_context()

    prompt = f"""## Section 1 — Identity & Personality
You are Samadhan Mitra (समाधान मित्र), a voice-first Hindi conversational assistant for Indian farmers.

PERSONALITY:
- You speak simple, warm Hindi (Khariboli dialect, Devanagari script)
- Your tone is like a caring, knowledgeable neighbor — NOT a government officer or doctor
- You are conservative with advice — always suggest confirming with local expert
- You NEVER diagnose medically, NEVER guarantee scheme eligibility
- Use the farmer's name when known
- Keep responses SHORT: 2-4 sentences for simple queries, max 5-6 for complex ones
- Always respond in Hindi (Devanagari script)

## Section 2 — Knowledge Tier Instructions

TIER 1 — VERIFIED KNOWLEDGE (in the knowledge sections below):
- Respond with confidence and specific details (chemical names, dosages, scheme criteria)
- These are hand-verified against ICAR/KVK/government sources

TIER 2 — GENERAL KNOWLEDGE (topics within agriculture/health/schemes but NOT in Tier 1):
- Provide general guidance and possible causes
- NEVER give specific chemical names, dosages, or medicine names
- ALWAYS prefix with "yeh meri aam samajh hai, apne Krishi Kendra/doctor se zaroor confirm karein"
- Offer to help further if they send a photo
- Provide the relevant referral (KVK number, sub-center location, etc.)

TIER 3 — OUT OF SCOPE (legal disputes, land records, police, financial investment, etc.):
- Warm acknowledgment + specific redirect with contact information
- "Yeh mere expertise se bahar hai, lekin aapke Block Development Officer isse help kar sakte hain."

CRITICAL RULES:
- NEVER fabricate information. NEVER make up scheme names, chemical names, or dosages.
- For health: NEVER diagnose. NEVER prescribe medicines except basic Paracetamol/ORS.
- For health: Always give one safe immediate action, state when to seek help, name facility type.

## Section 3 — Verified Knowledge

{knowledge}

## Section 4 — Profile Extraction

After EVERY response, you MUST output structured JSON inside <profile_update> tags.
This JSON must NEVER appear in the user-facing conversational response.
The <profile_update> block should come AFTER your Hindi response, separated clearly.

Format:
<profile_update>
{{
  "domain": "agriculture|health|schemes|general",
  "entities_extracted": {{
    "crop": null,
    "problem": null,
    "family_member": null,
    "scheme_name": null,
    "symptom": null,
    "action_taken": null,
    "location_mentioned": null
  }},
  "session_summary_update": "one line describing this exchange in English",
  "flags": []
}}
</profile_update>

Rules for profile_update:
- Only include fields that were actually mentioned in THIS conversation turn
- Set fields to null if not mentioned
- "flags" can include: "upcoming_deadline", "unresolved_problem", "emergency", "follow_up_needed"
- "session_summary_update" should be a brief English summary of what was discussed
- "domain" should be the PRIMARY domain of this exchange

## Section 5 — Conversation History

- Previous messages are provided as chat history
- Use them to resolve pronouns ("iske", "woh", "us")
- If session summaries are provided in the context, use them for cross-session continuity
- Maintain topic continuity unless the farmer explicitly changes subject

## Section 6 — Multi-Topic Handling

If the farmer mentions multiple domains in ONE message:
- Address each domain naturally in sequence (the order they mentioned them)
- Each domain response should be 1-2 sentences, connected naturally
- Output a single <profile_update> with the PRIMARY domain

## Section 7 — Farmer Context

{farmer_context if farmer_context else "No previous context available for this farmer."}
"""
    return prompt


def _parse_profile_update(response_text: str) -> tuple[str, dict | None]:
    """
    Separate the conversational response from the <profile_update> JSON block.
    Returns (clean_response, profile_update_dict).
    """
    # Extract content between <profile_update> tags
    pattern = r'<profile_update>\s*(.*?)\s*</profile_update>'
    match = re.search(pattern, response_text, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
        # Remove the profile_update block from the response
        clean_response = re.sub(pattern, '', response_text, flags=re.DOTALL).strip()

        try:
            profile_update = json.loads(json_str)
            return clean_response, profile_update
        except json.JSONDecodeError as e:
            print(f"[Profile update parse error] {e}")
            return clean_response, None
    else:
        return response_text.strip(), None


def chat(text: str, profile: dict, image_b64: str = None) -> dict:
    """
    Single Gemini call handling conversation + profile extraction.

    Returns:
        {
            "response": str,  # Hindi conversational response
            "domain": str,    # agriculture|health|schemes|general
            "profile_update": dict | None,  # extracted profile data
        }
    """
    import time
    from utils.profile_manager import get_context_for_prompt, get_chat_history

    client = _get_client()
    farmer_context = get_context_for_prompt(profile)
    system_prompt = _build_system_prompt(farmer_context)

    # Build chat history as text context (most compatible approach)
    chat_messages = get_chat_history(profile)
    history_text = ""
    if chat_messages:
        history_lines = []
        for msg in chat_messages:
            speaker = "Farmer" if msg["role"] == "user" else "Samadhan"
            history_lines.append(f"{speaker}: {msg['text']}")
        history_text = "\n\nRecent messages in this session:\n" + "\n".join(history_lines[-10:])

    # Build the full user message with history context
    full_message = f"{history_text}\n\nFarmer (new message): {text}" if history_text else text

    # Build content parts
    contents = []
    if image_b64:
        try:
            img_bytes = base64.b64decode(image_b64)
            # Detect mime type
            mime = "image/jpeg"
            if image_b64[:8].startswith("iVBOR"):
                mime = "image/png"
            elif image_b64[:8].startswith("UklGR"):
                mime = "image/webp"
            contents.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
        except Exception as e:
            print(f"[Image decode error] {e}")

    contents.append(full_message)

    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            # Single Gemini call with system prompt + message
            gemini_chat = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=2048,
                ),
            )

            raw_response = gemini_chat.text.strip()
            clean_response, profile_update = _parse_profile_update(raw_response)

            domain = "general"
            if profile_update:
                domain = profile_update.get("domain", "general")

            return {
                "response": clean_response,
                "domain": domain,
                "profile_update": profile_update,
            }

        except Exception as e:
            err_str = str(e)
            print(f"[Gemini attempt {attempt+1} error] {err_str}")
            
            # If 503 (high demand) or 429 (quota), retry unless it's the last attempt
            if ("503" in err_str or "429" in err_str) and attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
                
            return {
                "response": "माफ करें, अभी सर्वर पर लोड ज्यादा है। कृपया 10 सेकंड बाद दोबारा कोशिश करें।",
                "domain": "general",
                "profile_update": None,
            }


def generate_greeting(profile: dict) -> str:
    """
    Generate a proactive greeting for the farmer based on their profile.
    This is the Layer 4 — Perceived Memory feature.
    """
    from utils.profile_manager import get_context_for_prompt

    client = _get_client()
    farmer_context = get_context_for_prompt(profile)
    name = profile.get("name", "किसान भाई")

    prompt = f"""Given this farmer's profile and recent session summaries, generate a warm, brief Hindi greeting (in Devanagari script) that:
1. Addresses the farmer by name if known
2. References their most recent interaction naturally
3. Follows up on any unresolved problem
4. Mentions any upcoming deadline from their profile
Keep it to 2-3 sentences MAX. Speak like a caring neighbor checking in.
Do NOT include any JSON or profile_update tags. Only the greeting.

Farmer context:
{farmer_context if farmer_context else f"New farmer, no previous interactions. Just welcome {name} warmly."}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=256,
            ),
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Greeting error] {e}")
        return f"नमस्ते {name}! समाधान मित्र में आपका स्वागत है। आज मैं आपकी क्या मदद कर सकता हूँ?"


def generate_session_summary(messages: list) -> str:
    """Generate a one-line English summary of a session's messages."""
    client = _get_client()

    msg_text = "\n".join([
        f"{'Farmer' if m['role'] == 'user' else 'Samadhan'}: {m['text']}"
        for m in messages[:10]
    ])

    prompt = f"""Summarize this farmer conversation in one English line for future reference. Be concise and factual.

{msg_text}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=100,
            ),
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Summary error] {e}")
        return "Session completed."


def generate_partner_summary(profile: dict) -> str:
    """
    Generate a one-paragraph summary for the partner view.
    Written in simple Hindi for ASHA workers / Krishi officers.
    """
    from utils.profile_manager import get_context_for_prompt

    client = _get_client()
    farmer_context = get_context_for_prompt(profile)

    timeline = profile.get("timeline", [])
    timeline_text = ""
    if timeline:
        entries = []
        for t in timeline[:10]:
            entries.append(f"- {t.get('date', '?')} [{t.get('domain', '?')}]: {t.get('summary', '')} (Status: {t.get('status', '?')})")
        timeline_text = "\n".join(entries)

    flags = profile.get("flags", [])
    flags_text = ", ".join(flags) if flags else "None"

    prompt = f"""Given this farmer's profile and timeline, generate a one-paragraph summary in simple Hindi (Devanagari) that an ASHA worker would find useful before visiting the family.

Do NOT include any JSON or tags. Only the Hindi summary paragraph.

Profile context:
{farmer_context}

Timeline:
{timeline_text if timeline_text else "No timeline entries."}

Active flags: {flags_text}

Write a concise, practical summary paragraph in Hindi. Include: who the farmer is, recent problems, any unresolved issues, upcoming deadlines, and schemes status."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=300,
            ),
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Partner summary error] {e}")
        return "सारांश उपलब्ध नहीं है।"
