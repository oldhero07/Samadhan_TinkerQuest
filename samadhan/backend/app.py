"""
Samadhan — Main Flask Application.
Single-endpoint architecture: one /api/chat call handles all domains.
"""
import os
import re
import base64
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

from agents.gemini_engine import chat, generate_greeting, generate_session_summary, generate_partner_summary
from utils.groq_stt import transcribe as groq_transcribe
from utils.profile_manager import (
    get_profile, get_or_create_profile, save_profile,
    check_session_timeout, archive_session, add_message, apply_profile_update,
)

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://",
)

# Offline cache for when the farmer has no connectivity
OFFLINE_CACHE = [
    {"id": 1,  "query": "धान में कीड़े लग गए हैं",        "response": "धान में तना छेदक (stem borer) लगा होगा। क्लोरपायरीफोस 20EC की 2 मिली/लीटर छिड़काव करें।"},
    {"id": 2,  "query": "गेहूं की फसल पीली हो रही है",    "response": "Rust fungus या नाइट्रोजन की कमी। Mancozeb 2.5 ग्राम/लीटर स्प्रे या यूरिया 20-25 किग्रा/बीघा डालें।"},
    {"id": 3,  "query": "PM किसान सम्मान निधि",           "response": "PM किसान में ₹6000/साल मिलते हैं। pmkisan.gov.in पर रजिस्ट्रेशन करें।"},
    {"id": 4,  "query": "फसल बीमा कैसे करें",             "response": "PMFBY — बैंक या CSC केंद्र जाएं। बुवाई के 10 दिन के अंदर करवाएं।"},
    {"id": 5,  "query": "मिट्टी की जांच",                 "response": "KVK या कृषि विभाग में जाएं। मृदा स्वास्थ्य कार्ड मुफ्त मिलता है।"},
    {"id": 6,  "query": "सिंचाई पानी",                   "response": "धान में 5-7 दिन में एक बार, गेहूं में 6 बार सिंचाई पर्याप्त है।"},
    {"id": 7,  "query": "टमाटर रोग",                     "response": "झुलसा रोग हो सकता है। Mancozeb 2 ग्राम/लीटर का छिड़काव करें।"},
    {"id": 8,  "query": "सरसों माहू",                    "response": "Imidacloprid 0.3 मिली/लीटर स्प्रे करें।"},
    {"id": 9,  "query": "किसान क्रेडिट कार्ड",           "response": "KCC के लिए बैंक जाएं। 3 लाख तक 4% ब्याज पर लोन मिलता है।"},
    {"id": 10, "query": "मंडी भाव",                      "response": "agmarknet.gov.in पर आज के मंडी भाव देखें।"},
    {"id": 11, "query": "सोलर पंप",                      "response": "PM-KUSUM में 90% सब्सिडी पर सोलर पंप। कृषि विभाग से आवेदन करें।"},
    {"id": 12, "query": "बुखार दवाई",                    "response": "पानी ज्यादा पिएं, Paracetamol लें। 2 दिन से ज्यादा हो तो PHC जाएं।"},
    {"id": 13, "query": "आलू झुलसा",                     "response": "Mancozeb + Metalaxyl स्प्रे 10 दिन के अंतर पर करें।"},
    {"id": 14, "query": "यूरिया खाद",                    "response": "यूरिया कमी से पत्तियां पीली होती हैं। 20-25 किग्रा/बीघा डालें।"},
    {"id": 15, "query": "कपास बॉलवर्म",                  "response": "Bt कपास लगाएं या Cypermethrin स्प्रे करें।"},
]


def _validate_phone(raw: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", str(raw or "unknown").strip())
    if cleaned not in ("unknown", "") and len(re.sub(r"\D", "", cleaned)) < 5:
        return None
    return cleaned or "unknown"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Samadhan Mitra"})


@app.route("/chat", methods=["POST"])
@limiter.limit("30 per minute")
def chat_endpoint():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    phone = _validate_phone(data.get("phone", "unknown"))
    if phone is None:
        return jsonify({"error": "Invalid phone number"}), 400

    text = str(data.get("text", "")).strip()[:1000]
    audio_b64 = data.get("audio_b64")
    image_b64 = data.get("image_b64")

    if audio_b64 and len(audio_b64) > 14_000_000:
        return jsonify({"error": "Audio too large — max 60 seconds"}), 400
    if image_b64 and len(image_b64) > 9_000_000:
        return jsonify({"error": "Image too large — max 5MB"}), 400

    transcription = None

    if audio_b64 and not text:
        try:
            audio_bytes = base64.b64decode(audio_b64)
            text = groq_transcribe(audio_bytes)
            transcription = text
            if not text:
                return jsonify({"error": "आवाज़ समझ नहीं आई — कृपया दोबारा बोलें"}), 422
        except Exception as e:
            log.error(f"[STT error] {e}")
            return jsonify({"error": "आवाज़ प्रोसेस नहीं हो पाई"}), 422

    if not text:
        return jsonify({"error": "कोई सवाल नहीं मिला"}), 400

    profile = get_or_create_profile(phone)

    profile, timed_out = check_session_timeout(profile)
    if timed_out:
        old_messages = profile.get("active_session", {}).get("messages", [])
        if old_messages:
            summary = generate_session_summary(old_messages)
            profile["active_session"]["summary"] = summary
        profile = archive_session(profile)

    profile = add_message(profile, "user", text, has_image=bool(image_b64))

    result = chat(text, profile, image_b64=image_b64)
    response_text = result["response"]
    domain = result["domain"]
    profile_update = result.get("profile_update")

    entities = profile_update.get("entities_extracted", {}) if profile_update else {}
    profile = add_message(profile, "assistant", response_text, domain=domain, entities=entities)

    if profile_update:
        profile = apply_profile_update(profile, profile_update)

    save_profile(phone, profile)

    response = {"response": response_text, "domain": domain}
    if transcription:
        response["transcription"] = transcription
    return jsonify(response)


@app.route("/greeting", methods=["POST"])
@limiter.limit("20 per minute")
def greeting_endpoint():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    phone = _validate_phone(data.get("phone", "unknown"))
    if phone is None:
        return jsonify({"error": "Invalid phone number"}), 400

    profile = get_or_create_profile(phone)

    profile, timed_out = check_session_timeout(profile)
    if timed_out:
        old_messages = profile.get("active_session", {}).get("messages", [])
        if old_messages:
            summary = generate_session_summary(old_messages)
            profile["active_session"]["summary"] = summary
        profile = archive_session(profile)
        save_profile(phone, profile)

    greeting = generate_greeting(profile)
    return jsonify({"greeting": greeting})


@app.route("/profile/<phone>", methods=["GET"])
def profile_endpoint(phone):
    """Partner view: returns farmer profile by phone number."""
    token = request.headers.get("X-Partner-Token", "")
    expected = os.getenv("PARTNER_TOKEN", "samadhan2026")
    if token != expected:
        return jsonify({"error": "Unauthorized"}), 401
    data = get_profile(phone)
    if not data:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(data)


@app.route("/partner/<phone>/summary", methods=["GET"])
def partner_summary_endpoint(phone):
    token = request.headers.get("X-Partner-Token", "")
    expected = os.getenv("PARTNER_TOKEN", "samadhan2026")
    if token != expected:
        return jsonify({"error": "Unauthorized"}), 401

    profile = get_profile(phone)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    summary = generate_partner_summary(profile)
    return jsonify({"summary": summary})


@app.route("/partner/<phone>/flag", methods=["POST"])
def partner_flag_endpoint(phone):
    """Partner: add or remove a flag on a farmer profile."""
    token = request.headers.get("X-Partner-Token", "")
    expected = os.getenv("PARTNER_TOKEN", "samadhan2026")
    if token != expected:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    flag = str(data.get("flag", "")).strip()
    action = str(data.get("action", "add")).strip()  # "add" or "remove"
    valid_flags = {"follow_up_needed", "emergency", "upcoming_deadline", "unresolved_problem", "resolved"}
    if flag not in valid_flags:
        return jsonify({"error": f"Invalid flag. Use one of: {', '.join(sorted(valid_flags))}"}), 400

    profile = get_profile(phone)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    flags = profile.setdefault("flags", [])
    if action == "remove":
        profile["flags"] = [f for f in flags if f != flag]
    else:
        if flag not in flags:
            flags.append(flag)

    save_profile(phone, profile)
    log.info(f"[Partner] Flag '{flag}' {action}ed for phone={phone}")
    return jsonify({"success": True, "flags": profile["flags"]})


@app.route("/offline", methods=["GET"])
def offline_cache():
    return jsonify({"cache": OFFLINE_CACHE})


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5001))
    app.run(debug=True, port=port)
