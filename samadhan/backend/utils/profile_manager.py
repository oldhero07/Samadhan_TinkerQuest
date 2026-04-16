"""
Farmer Profile Manager — SQLite-backed via SQLAlchemy.
Public API is identical to the old JSON-file version so no other files need changes.
"""
from __future__ import annotations
import uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session as DBSession

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import init_db, SessionLocal, Farmer, ChatSession, Message

log = logging.getLogger(__name__)

SESSION_TIMEOUT_MINUTES = 30
MAX_SESSION_MESSAGES = 20
MAX_RECENT_SESSIONS = 10

# Initialise DB tables on import
init_db()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _db() -> DBSession:
    return SessionLocal()


def _get_active_session(db: DBSession, phone: str):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.phone == phone, ChatSession.ended_at == None)
        .order_by(ChatSession.started_at.desc())
        .first()
    )
    if not session:
        return None, []
    messages = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return session, messages


def _row_to_profile(farmer: Farmer, session, messages: list) -> dict:
    """Assemble the profile dict that gemini_engine expects."""
    active_session = {}
    if session:
        active_session = {
            "session_id": session.id,
            "session_start": session.started_at.isoformat(),
            "last_active": session.ended_at.isoformat() if session.ended_at else session.started_at.isoformat(),
            "messages": [
                {
                    "role": m.role,
                    "text": m.text,
                    "domain": m.domain,
                    "has_image": bool(m.has_image),
                    "timestamp": m.created_at.isoformat(),
                }
                for m in messages
            ],
        }

    pd = farmer.profile_data or {}
    return {
        "phone": farmer.phone,
        "name": farmer.name or "",
        "village": farmer.village or "",
        "district": farmer.district or "",
        "registered_date": farmer.registered_at.strftime("%Y-%m-%d"),
        "active_session": active_session,
        "recent_sessions": pd.get("recent_sessions", []),
        "profile": pd.get("profile", {
            "agriculture": {"primary_crops": [], "land_area": "", "current_season": "", "reported_problems": []},
            "health": {"family_queries": []},
            "schemes": {},
        }),
        "flags": pd.get("flags", []),
        "timeline": pd.get("timeline", []),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def get_profile(phone: str):
    db = _db()
    try:
        farmer = db.query(Farmer).filter(Farmer.phone == phone).first()
        if not farmer:
            return None
        session, messages = _get_active_session(db, phone)
        return _row_to_profile(farmer, session, messages)
    finally:
        db.close()


def get_or_create_profile(phone: str) -> dict:
    db = _db()
    try:
        farmer = db.query(Farmer).filter(Farmer.phone == phone).first()
        if not farmer:
            farmer = Farmer(phone=phone, registered_at=datetime.utcnow(), profile_data={})
            db.add(farmer)
            db.commit()
            db.refresh(farmer)
            log.info(f"[Profile] Created new farmer: {phone}")
        session, messages = _get_active_session(db, phone)
        return _row_to_profile(farmer, session, messages)
    finally:
        db.close()


def save_profile(phone: str, profile: dict) -> None:
    db = _db()
    try:
        farmer = db.query(Farmer).filter(Farmer.phone == phone).first()
        if not farmer:
            farmer = Farmer(phone=phone, registered_at=datetime.utcnow(), profile_data={})
            db.add(farmer)

        farmer.name = profile.get("name") or farmer.name or ""
        farmer.village = profile.get("village") or farmer.village or ""
        farmer.district = profile.get("district") or farmer.district or ""

        pd = dict(farmer.profile_data or {})
        pd["recent_sessions"] = profile.get("recent_sessions", pd.get("recent_sessions", []))
        pd["profile"] = profile.get("profile", pd.get("profile", {}))
        pd["flags"] = profile.get("flags", pd.get("flags", []))
        pd["timeline"] = profile.get("timeline", pd.get("timeline", []))
        farmer.profile_data = pd

        db.commit()
    except Exception as e:
        log.error(f"[Profile] save_profile error for {phone}: {e}")
        db.rollback()
    finally:
        db.close()


def check_session_timeout(profile: dict) -> tuple:
    active = profile.get("active_session", {})
    if not active:
        return profile, False
    last_active_str = active.get("last_active", active.get("session_start", ""))
    if not last_active_str:
        return profile, False
    try:
        last_active = datetime.fromisoformat(last_active_str)
        timed_out = datetime.utcnow() - last_active > timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        return profile, timed_out
    except Exception:
        return profile, False


def archive_session(profile: dict) -> dict:
    active = profile.get("active_session", {})
    if not active:
        return profile
    session_id = active.get("session_id")
    if not session_id:
        return profile

    db = _db()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session and session.ended_at is None:
            session.ended_at = datetime.utcnow()
            db.commit()

        recent_entry = {
            "session_id": session_id,
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "summary": active.get("summary", "Session completed."),
            "domain": active.get("domain", "general"),
            "key_entities": [],
        }
        recent = profile.get("recent_sessions", [])
        recent.insert(0, recent_entry)
        profile["recent_sessions"] = recent[:MAX_RECENT_SESSIONS]
        profile["active_session"] = {}
    except Exception as e:
        log.error(f"[Profile] archive_session error: {e}")
        db.rollback()
    finally:
        db.close()
    return profile


def add_message(profile: dict, role: str, text: str, has_image: bool = False, domain: str = "general", entities: dict = None) -> dict:
    db = _db()
    try:
        phone = profile.get("phone", "unknown")
        active = profile.get("active_session", {})
        session_id = active.get("session_id")

        if not session_id:
            session_id = str(uuid.uuid4())
            db.add(ChatSession(id=session_id, phone=phone, started_at=datetime.utcnow()))
            db.commit()
            profile["active_session"] = {
                "session_id": session_id,
                "session_start": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat(),
                "messages": [],
            }

        db.add(Message(
            session_id=session_id, phone=phone, role=role, text=text,
            domain=domain, has_image=int(has_image), created_at=datetime.utcnow(),
        ))

        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.ended_at = datetime.utcnow()
        db.commit()

        msgs = profile["active_session"].get("messages", [])
        msgs.append({"role": role, "text": text, "domain": domain, "has_image": has_image, "timestamp": datetime.utcnow().isoformat()})
        if len(msgs) > MAX_SESSION_MESSAGES:
            msgs = msgs[-MAX_SESSION_MESSAGES:]
        profile["active_session"]["messages"] = msgs
        profile["active_session"]["last_active"] = datetime.utcnow().isoformat()
    except Exception as e:
        log.error(f"[Profile] add_message error: {e}")
        db.rollback()
    finally:
        db.close()
    return profile


def apply_profile_update(profile: dict, update: dict) -> dict:
    if not update:
        return profile
    if update.get("name"):   profile["name"] = update["name"]
    if update.get("village"): profile["village"] = update["village"]
    if update.get("district"): profile["district"] = update["district"]

    sub = profile.setdefault("profile", {})
    ag = sub.setdefault("agriculture", {"primary_crops": [], "land_area": "", "current_season": "", "reported_problems": []})
    if update.get("crop") and update["crop"] not in ag["primary_crops"]:
        ag["primary_crops"].append(update["crop"])
    if update.get("land_area"): ag["land_area"] = update["land_area"]
    if update.get("problem") and update["problem"] not in ag.get("reported_problems", []):
        ag.setdefault("reported_problems", []).append(update["problem"])

    health = sub.setdefault("health", {"family_queries": []})
    if update.get("health_query") and update["health_query"] not in health["family_queries"]:
        health["family_queries"].append(update["health_query"])

    schemes = sub.setdefault("schemes", {})
    if update.get("scheme"):
        schemes[update["scheme"]] = {"status": update.get("scheme_status", "enquired"), "last_checked": datetime.utcnow().strftime("%Y-%m-%d")}

    flags = profile.setdefault("flags", [])
    for flag in update.get("add_flags", []):
        if flag not in flags: flags.append(flag)
    for flag in update.get("remove_flags", []):
        if flag in flags: flags.remove(flag)

    if update.get("timeline_entry"):
        timeline = profile.setdefault("timeline", [])
        timeline.insert(0, {"date": datetime.utcnow().strftime("%Y-%m-%d"), "domain": update.get("domain", "general"), "summary": update["timeline_entry"], "status": update.get("timeline_status", "✅ हल")})
        profile["timeline"] = timeline[:50]
    return profile


def get_context_for_prompt(profile: dict) -> str:
    parts = []
    if profile.get("name"): parts.append(f"किसान का नाम: {profile['name']}")
    if profile.get("village") or profile.get("district"):
        parts.append(f"स्थान: {profile.get('village','')}, {profile.get('district','')}")
    ag = profile.get("profile", {}).get("agriculture", {})
    if ag.get("primary_crops"): parts.append(f"मुख्य फसलें: {', '.join(ag['primary_crops'])}")
    if ag.get("reported_problems"): parts.append(f"पहले बताई समस्याएं: {', '.join(ag['reported_problems'][-3:])}")
    recent = profile.get("recent_sessions", [])
    summaries = [s.get("summary", "") for s in recent[:3] if s.get("summary")]
    if summaries: parts.append("पिछली बातचीत: " + " | ".join(summaries))
    if profile.get("flags"): parts.append(f"फ्लैग: {', '.join(profile['flags'])}")
    return "\n".join(parts)


def get_chat_history(profile: dict) -> list:
    return profile.get("active_session", {}).get("messages", [])
