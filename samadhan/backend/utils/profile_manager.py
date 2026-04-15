"""
Farmer Profile Manager — Four-Layer Memory System.
Profiles stored as JSON files in backend/profiles/<phone>.json

Implements:
  Layer 1: Conversational memory (active session messages)
  Layer 2: Session memory (AI-generated session summaries)
  Layer 3: Life memory (structured profile facts)
  Layer 4: Perceived memory (proactive greeting data)
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

PROFILES_DIR = Path(__file__).parent.parent / "profiles"
PROFILES_DIR.mkdir(exist_ok=True)

SESSION_TIMEOUT_MINUTES = 30
MAX_SESSION_MESSAGES = 20  # 10 pairs
MAX_RECENT_SESSIONS = 10


def _profile_path(phone: str) -> Path:
    safe = "".join(c for c in phone if c.isdigit() or c == "+")
    return PROFILES_DIR / f"{safe}.json"


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _default_profile(phone: str) -> dict:
    """Create a blank profile with the full schema."""
    return {
        "phone": phone,
        "name": None,
        "village": None,
        "block": None,
        "district": None,
        "registered_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "active_session": {
            "session_id": f"sess_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            "session_start": _now_iso(),
            "last_active": _now_iso(),
            "messages": [],
        },
        "recent_sessions": [],
        "profile": {
            "agriculture": {
                "primary_crops": [],
                "land_area": None,
                "current_season": None,
                "reported_problems": [],
            },
            "health": {
                "family_queries": [],
            },
            "schemes": {},
        },
        "flags": [],
        "timeline": [],
    }


def get_profile(phone: str) -> dict:
    """Returns farmer profile dict, or creates a new one if not found."""
    path = _profile_path(phone)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_or_create_profile(phone: str) -> dict:
    """Returns existing profile or creates a new default one."""
    profile = get_profile(phone)
    if not profile:
        profile = _default_profile(phone)
        save_profile(phone, profile)
    return profile


def save_profile(phone: str, profile: dict):
    """Persist profile to disk."""
    _profile_path(phone).write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def check_session_timeout(profile: dict) -> bool:
    """Check if current session has timed out (30-min gap)."""
    active = profile.get("active_session")
    if not active or not active.get("last_active"):
        return True
    try:
        last = datetime.fromisoformat(active["last_active"])
        return (datetime.utcnow() - last) > timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    except Exception:
        return True


def archive_session(profile: dict, summary: str = None) -> dict:
    """
    Archive the active session into recent_sessions.
    Creates a new empty active session.
    """
    active = profile.get("active_session", {})
    messages = active.get("messages", [])

    if messages:
        # Determine domain from messages
        domains = []
        for msg in messages:
            d = msg.get("domain")
            if d and d != "general":
                domains.append(d)
        domain = domains[0] if domains else "general"

        # Extract key entities from messages
        key_entities = {}
        for msg in messages:
            entities = msg.get("entities", {})
            if entities:
                for k, v in entities.items():
                    if v:
                        key_entities[k] = v

        session_record = {
            "session_id": active.get("session_id", "unknown"),
            "date": active.get("session_start", _now_iso())[:10],
            "summary": summary or "Session completed.",
            "domain": domain,
            "key_entities": key_entities,
        }

        recent = profile.get("recent_sessions", [])
        recent.insert(0, session_record)
        profile["recent_sessions"] = recent[:MAX_RECENT_SESSIONS]

        # Also add to timeline
        timeline_entry = {
            "date": session_record["date"],
            "domain": domain,
            "summary": summary or "Session completed.",
            "status": "resolved",
        }
        timeline = profile.get("timeline", [])
        timeline.insert(0, timeline_entry)
        profile["timeline"] = timeline[:50]

    # Start new session
    profile["active_session"] = {
        "session_id": f"sess_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
        "session_start": _now_iso(),
        "last_active": _now_iso(),
        "messages": [],
    }

    return profile


def add_message(profile: dict, role: str, text: str, domain: str = None,
                has_image: bool = False, entities: dict = None) -> dict:
    """Add a message to the active session."""
    active = profile.get("active_session")
    if not active:
        profile["active_session"] = {
            "session_id": f"sess_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            "session_start": _now_iso(),
            "last_active": _now_iso(),
            "messages": [],
        }
        active = profile["active_session"]

    msg = {
        "role": role,
        "text": text,
        "timestamp": _now_iso(),
    }
    if domain:
        msg["domain"] = domain
    if has_image:
        msg["has_image"] = True
    if entities:
        msg["entities"] = entities

    active["messages"].append(msg)
    active["last_active"] = _now_iso()

    # Trim if too many messages (keep last MAX_SESSION_MESSAGES)
    if len(active["messages"]) > MAX_SESSION_MESSAGES:
        active["messages"] = active["messages"][-MAX_SESSION_MESSAGES:]

    return profile


def apply_profile_update(profile: dict, update: dict) -> dict:
    """
    Apply a profile_update JSON (from Gemini response) to the profile.
    Merges entities into the structured profile section.
    """
    if not update:
        return profile

    entities = update.get("entities_extracted", {})
    domain = update.get("domain", "general")
    flags = update.get("flags", [])
    summary = update.get("session_summary_update", "")

    prof = profile.setdefault("profile", {})

    # Agriculture entities
    if entities.get("crop"):
        ag = prof.setdefault("agriculture", {"primary_crops": [], "reported_problems": []})
        crop = entities["crop"]
        if crop not in ag.get("primary_crops", []):
            ag.setdefault("primary_crops", []).append(crop)

        if entities.get("problem"):
            problem_entry = {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "crop": crop,
                "problem": entities["problem"],
                "symptom_described": entities.get("symptom", ""),
                "advice_given": entities.get("action_taken", ""),
                "status": "advised_treatment",
                "follow_up_needed": True,
            }
            ag.setdefault("reported_problems", []).insert(0, problem_entry)

    # Health entities
    if entities.get("symptom") and not entities.get("crop"):
        health = prof.setdefault("health", {"family_queries": []})
        health_entry = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "member": entities.get("family_member", "self"),
            "symptom": entities["symptom"],
            "action": entities.get("action_taken", ""),
            "follow_up_needed": True,
        }
        health.setdefault("family_queries", []).insert(0, health_entry)

    # Scheme entities
    if entities.get("scheme_name"):
        schemes = prof.setdefault("schemes", {})
        scheme_key = entities["scheme_name"].lower().replace(" ", "_").replace("-", "_")
        if scheme_key not in schemes:
            schemes[scheme_key] = {"status": "enquired", "last_checked": datetime.utcnow().strftime("%Y-%m-%d")}

    # Name / location extraction
    if entities.get("location_mentioned"):
        if not profile.get("village"):
            profile["village"] = entities["location_mentioned"]

    # Merge flags
    if flags:
        existing_flags = set(profile.get("flags", []))
        existing_flags.update(flags)
        profile["flags"] = list(existing_flags)

    # Update timeline with latest domain interaction summary
    if summary and domain != "general":
        timeline = profile.setdefault("timeline", [])
        timeline_entry = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "domain": domain,
            "summary": summary,
            "status": "unresolved" if any("unresolved" in f for f in flags) else "active",
        }
        timeline.insert(0, timeline_entry)
        profile["timeline"] = timeline[:50]

    return profile


def get_context_for_prompt(profile: dict) -> str:
    """
    Build a context string from the profile for injection into system prompt.
    Includes recent session summaries and key profile facts.
    """
    lines = []

    # Farmer identity
    name = profile.get("name", "Unknown")
    village = profile.get("village", "")
    if name and name != "Unknown":
        lines.append(f"Farmer name: {name}")
    if village:
        lines.append(f"Village: {village}")

    # Recent session summaries (Layer 2)
    recent = profile.get("recent_sessions", [])[:3]
    if recent:
        lines.append("\nPrevious interactions with this farmer:")
        for s in recent:
            lines.append(f"- {s.get('date', '?')}: {s.get('summary', 'No summary')}")

    # Profile facts (Layer 3)
    prof = profile.get("profile", {})
    ag = prof.get("agriculture", {})
    if ag.get("primary_crops"):
        lines.append(f"\nCrops: {', '.join(ag['primary_crops'])}")
    if ag.get("land_area"):
        lines.append(f"Land: {ag['land_area']}")

    schemes = prof.get("schemes", {})
    if schemes:
        scheme_lines = []
        for k, v in schemes.items():
            scheme_lines.append(f"{k}: {v.get('status', 'unknown')}")
        lines.append(f"Schemes: {', '.join(scheme_lines)}")

    # Flags
    flags = profile.get("flags", [])
    if flags:
        lines.append(f"\nActive flags: {', '.join(flags)}")

    return "\n".join(lines) if lines else ""


def get_chat_history(profile: dict) -> list:
    """Get active session messages formatted for Gemini chat history."""
    active = profile.get("active_session", {})
    messages = active.get("messages", [])
    return messages
