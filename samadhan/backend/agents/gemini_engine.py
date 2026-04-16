from __future__ import annotations
"""
Gemini Engine — Single-call LLM architecture.
Replaces the old Sunno/Khet/Haq multi-agent setup.

One Gemini call handles:
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
import logging
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai import types

log = logging.getLogger(__name__)

_client = None

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

# Model cascade: primary is latest flash; fallback is lite version
PRIMARY_MODEL   = "gemini-2.5-flash"
FALLBACK_MODEL  = "gemini-2.5-flash-lite"

# Knowledge cache — load once at startup, not per call
_KNOWLEDGE_CACHE: dict = {}


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _load_json(filename: str) -> list | dict:
    if filename in _KNOWLEDGE_CACHE:
        return _KNOWLEDGE_CACHE[filename]
    path = KNOWLEDGE_DIR / filename
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            _KNOWLEDGE_CACHE[filename] = data
            return data
        except Exception:
            return []
    return []


def _current_season_hint() -> str:
    """Return a brief farming-season context string based on current month."""
    month = datetime.now().month
    if month in (6, 7, 8):
        return "अभी खरीफ बुवाई का मौसम है (जून-अगस्त)। धान, मक्का, कपास, सोयाबीन की बुवाई चल रही है।"
    elif month in (9, 10):
        return "खरीफ फसल की देखभाल का समय है। धान में बाली आ रही है।"
    elif month in (11, 12):
        return "रबी बुवाई का मौसम है (नवंबर-दिसंबर)। गेहूं, सरसों, चना की बुवाई चल रही है।"
    elif month in (1, 2, 3):
        return "रबी फसल की देखभाल का समय है। गेहूं में बाली आ रही है।"
    elif month in (4, 5):
        return "रबी कटाई और खरीफ की तैयारी का समय है (अप्रैल-मई)। गेहूं कट रहा है, धान के लिए खेत तैयार करें।"
    return ""


def _build_knowledge_context(district: str = "") -> str:
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

    # Referral map — district-aware
    referrals_data = _load_json("referrals.json")
    if referrals_data:
        district_key = district.lower().strip() if district else ""
        local_refs = referrals_data.get(district_key, []) if district_key else []
        generic_refs = referrals_data.get("generic", [])
        all_refs = local_refs + generic_refs if local_refs else generic_refs

        district_label = f"({district.title()} जिला)" if district_key and local_refs else "(सामान्य हेल्पलाइन)"
        lines = [f"=== REFERRAL MAP {district_label} ==="]
        for r in all_refs:
            entry = f"- {r.get('name', 'Unknown')}"
            if r.get('type'):
                entry += f" ({r['type']})"
            if r.get('address'):
                entry += f" — {r['address']}"
            if r.get('phone'):
                entry += f" | फोन: {r['phone']}"
            if r.get('hours'):
                entry += f" | समय: {r['hours']}"
            lines.append(entry)
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def _build_system_prompt(farmer_context: str = "", district: str = "") -> str:
    """Build the complete system prompt with all sections."""
    knowledge = _build_knowledge_context(district=district)
    season_hint = _current_season_hint()
    current_month = datetime.now().strftime("%B %Y")

    prompt = f"""## Section 1 — Identity & Personality
You are Samadhan Mitra (समाधान मित्र), a voice-first Hindi assistant for Indian farmers in Uttarakhand/UP.

PERSONALITY:
- Speak warm, simple Hindi (Khariboli). Use "आप" for respect but keep sentences short and village-friendly.
- Tone like a caring, knowledgeable neighbor — NOT a government officer, doctor, or textbook.
- You are conservative with advice — always suggest confirming with local KVK/expert.
- Use the farmer's name when known (e.g., "राम भाई,").
- NEVER diagnose medically. NEVER guarantee scheme eligibility. NEVER fabricate data.

RESPONSE LENGTH RULES (strictly follow):
- Simple queries (one crop problem, one scheme name): MAX 60 words in Hindi.
- Complex queries (multiple issues, detailed advice): MAX 100 words.
- Always end with one short next step (e.g., "KVK से मिलें", "pmkisan.gov.in देखें").
- NEVER write bullet-point lists — speak naturally like a conversation.

CURRENT DATE & SEASON CONTEXT:
- Today: {current_month}
- {season_hint}

## Section 2 — Knowledge Tier Instructions

TIER 1 — VERIFIED KNOWLEDGE (in the knowledge sections below):
- Respond with confidence and specific details (chemical names, dosages, scheme criteria).
- These are hand-verified against ICAR/KVK/government sources.

TIER 2 — GENERAL KNOWLEDGE (topics within agriculture/health/schemes but NOT in Tier 1):
- Provide general guidance and possible causes.
- NEVER give specific chemical names, dosages, or medicine names.
- ALWAYS prefix with: "मेरी जानकारी के अनुसार — लेकिन अपने कृषि केंद्र/डॉक्टर से ज़रूर पूछें।"
- Offer to help further if they send a photo.

TIER 3 — OUT OF SCOPE (legal disputes, land records, police, financial investment, etc.):
- Warm acknowledgment + specific redirect.
- "यह मेरी जानकारी से बाहर है, लेकिन आपके Block Development Officer इसमें मदद कर सकते हैं।"

## Section 3 — Verified Knowledge

{knowledge}

## Section 4 — Profile Extraction (CRITICAL FORMAT RULE)

IMPORTANT: The <profile_update> block MUST appear AFTER your Hindi response on a NEW LINE.
It must NEVER be part of the conversational text the farmer sees.
Do NOT wrap it in markdown code blocks.

Format (always output this after every response):
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
  "name": null,
  "village": null,
  "district": null,
  "session_summary_update": "one English sentence describing this exchange",
  "flags": []
}}
</profile_update>

Rules:
- Only include fields actually mentioned in this turn; set others to null.
- "flags" options: "upcoming_deadline", "unresolved_problem", "emergency", "follow_up_needed"
- Extract name/village/district if the farmer mentions them naturally.

## Section 5 — Conversation History

- Previous messages are provided as chat history.
- Use them to resolve pronouns ("इसमें", "उस फसल में", "वो दवाई").
- Maintain topic continuity unless farmer changes subject.

## Section 6 — Multi-Topic Handling

If farmer mentions multiple domains:
- Address each domain in 1-2 sentences, connected naturally.
- Single <profile_update> with the PRIMARY domain.

## Section 7 — Farmer Context

{farmer_context if farmer_context else "नया किसान — पहली बातचीत।"}
"""
    return prompt


def _parse_profile_update(response_text: str) -> tuple[str, dict | None]:
    """
    Separate the conversational response from the <profile_update> JSON block.
    Returns (clean_response, profile_update_dict).
    """
    pattern = r'<profile_update>\s*(.*?)\s*</profile_update>'
    match = re.search(pattern, response_text, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
        clean_response = re.sub(pattern, '', response_text, flags=re.DOTALL).strip()

        try:
            profile_update = json.loads(json_str)
            return clean_response, profile_update
        except json.JSONDecodeError as e:
            log.warning(f"[Profile update parse error] {e}")
            return clean_response, None
    else:
        return response_text.strip(), None


def _call_model(client, model: str, contents, system_prompt: str, max_tokens: int = 1024) -> str:
    """Call a specific Gemini model and return raw text."""
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text.strip()


def chat(text: str, profile: dict, image_b64: str = None) -> dict:
    """
    Single Gemini call handling conversation + profile extraction.

    Returns:
        {
            "response": str,  # Hindi conversational response
            "domain": str,    # agriculture|health|schemes|general
            "profile_update": dict | None,
        }
    """
    import time
    from utils.profile_manager import get_context_for_prompt, get_chat_history

    client = _get_client()
    farmer_context = get_context_for_prompt(profile)
    district = profile.get("district", "") or ""
    system_prompt = _build_system_prompt(farmer_context, district=district)

    # Build chat history as context
    chat_messages = get_chat_history(profile)
    history_text = ""
    if chat_messages:
        history_lines = []
        for msg in chat_messages:
            speaker = "Farmer" if msg["role"] == "user" else "Samadhan"
            history_lines.append(f"{speaker}: {msg['text']}")
        history_text = "\n\nRecent conversation:\n" + "\n".join(history_lines[-10:])

    full_message = f"{history_text}\n\nFarmer (new message): {text}" if history_text else text

    # Build content parts
    contents = []
    if image_b64:
        try:
            img_bytes = base64.b64decode(image_b64)
            mime = "image/jpeg"
            if image_b64[:8].startswith("iVBOR"):
                mime = "image/png"
            elif image_b64[:8].startswith("UklGR"):
                mime = "image/webp"
            contents.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
        except Exception as e:
            log.warning(f"[Image decode error] {e}")

    contents.append(full_message)

    # Model cascade: PRIMARY → FALLBACK
    models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]
    last_err = None

    for model in models_to_try:
        for attempt in range(2):  # 2 attempts per model
            try:
                raw_response = _call_model(client, model, contents, system_prompt, max_tokens=1024)
                clean_response, profile_update = _parse_profile_update(raw_response)

                domain = "general"
                if profile_update:
                    domain = profile_update.get("domain", "general")

                log.info(f"[Gemini] model={model} domain={domain} chars={len(clean_response)}")
                return {
                    "response": clean_response,
                    "domain": domain,
                    "profile_update": profile_update,
                }

            except Exception as e:
                last_err = str(e)
                log.warning(f"[Gemini] model={model} attempt={attempt+1} error: {last_err[:120]}")

                if "429" in last_err:
                    # Quota hit — don't retry same model, move to next model
                    break
                elif "503" in last_err or "500" in last_err:
                    # Server overload — brief wait then retry
                    time.sleep(1.5 * (attempt + 1))
                    continue
                else:
                    break

    # All models failed — return contextual fallback
    if last_err and "429" in last_err:
        fallback_msg = "अभी बहुत सारे लोग पूछ रहे हैं, थोड़ी देर बाद कोशिश करें।"
    elif last_err and any(x in last_err for x in ["503", "timeout", "connection"]):
        fallback_msg = "नेटवर्क में दिक्कत है, कृपया दोबारा कोशिश करें।"
    else:
        fallback_msg = "कुछ तकनीकी गड़बड़ी हुई। थोड़ी देर बाद पूछें।"

    log.error(f"[Gemini] All models failed. last_err={last_err[:200] if last_err else 'unknown'}")
    return {
        "response": fallback_msg,
        "domain": "general",
        "profile_update": None,
    }


def generate_greeting(profile: dict) -> str:
    """Generate a proactive greeting based on farmer profile."""
    from utils.profile_manager import get_context_for_prompt

    client = _get_client()
    farmer_context = get_context_for_prompt(profile)
    name = profile.get("name", "किसान भाई")

    prompt = f"""Given this farmer's profile, generate a warm Hindi greeting (Devanagari script) that:
1. Addresses the farmer by name if known
2. References their most recent interaction naturally (1 line)
3. Follows up on any unresolved problem
4. Mentions any upcoming deadline

Keep it to 2-3 sentences MAX. Speak like a caring neighbor. Do NOT include any JSON or tags.

Farmer context:
{farmer_context if farmer_context else f"New farmer. Welcome {name} warmly in Hindi."}
"""

    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=200),
            )
            return response.text.strip()
        except Exception as e:
            log.warning(f"[Greeting] model={model} error: {e}")

    return f"नमस्ते {name}! समाधान मित्र में आपका स्वागत है। आज मैं आपकी क्या मदद कर सकता हूँ?"


def generate_session_summary(messages: list) -> str:
    """Generate a one-line English summary of a session's messages."""
    client = _get_client()

    msg_text = "\n".join([
        f"{'Farmer' if m['role'] == 'user' else 'Samadhan'}: {m['text']}"
        for m in messages[:10]
    ])

    prompt = f"""Summarize this farmer conversation in one English sentence for future reference. Be concise and factual.

{msg_text}"""

    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=100),
            )
            return response.text.strip()
        except Exception as e:
            log.warning(f"[Summary] model={model} error: {e}")

    return "Session completed."


def generate_partner_summary(profile: dict) -> str:
    """Generate a one-paragraph Hindi summary for partner/ASHA worker view."""
    from utils.profile_manager import get_context_for_prompt

    client = _get_client()
    farmer_context = get_context_for_prompt(profile)

    timeline = profile.get("timeline", [])
    timeline_text = ""
    if timeline:
        entries = [
            f"- {t.get('date', '?')} [{t.get('domain', '?')}]: {t.get('summary', '')} (Status: {t.get('status', '?')})"
            for t in timeline[:10]
        ]
        timeline_text = "\n".join(entries)

    flags = profile.get("flags", [])
    flags_text = ", ".join(flags) if flags else "None"

    prompt = f"""Given this farmer's profile, generate a one-paragraph summary in simple Hindi (Devanagari) useful for an ASHA worker before a home visit. Include: who the farmer is, recent problems, unresolved issues, upcoming deadlines, schemes status. Do NOT include JSON or tags.

Profile:
{farmer_context}

Timeline:
{timeline_text if timeline_text else "No timeline."}

Active flags: {flags_text}"""

    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=300),
            )
            return response.text.strip()
        except Exception as e:
            log.warning(f"[PartnerSummary] model={model} error: {e}")

    return "सारांश उपलब्ध नहीं है।"
