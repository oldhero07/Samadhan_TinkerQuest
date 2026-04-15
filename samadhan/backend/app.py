"""
Samadhan — Main Flask Application.
Single-endpoint architecture: one /api/chat call handles all domains.
"""
import os
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from agents.gemini_engine import chat, generate_greeting, generate_session_summary, generate_partner_summary
from utils.groq_stt import transcribe as groq_transcribe
from utils.profile_manager import (
    get_profile, get_or_create_profile, save_profile,
    check_session_timeout, archive_session, add_message, apply_profile_update,
)

load_dotenv()

app = Flask(__name__)
CORS(app)

# Offline cache for when the farmer has no connectivity
OFFLINE_CACHE = [
    {"id": 1, "query": "धान में कीड़े लग गए हैं", "response": "धान में तना छेदक (stem borer) कीड़ा लगा होगा। क्लोरपायरीफोस 20EC की 2 मिली प्रति लीटर पानी में मिलाकर छिड़काव करें। सुबह या शाम को करें।"},
    {"id": 2, "query": "गेहूं की फसल पीली हो रही है", "response": "गेहूं की पत्तियां पीली होना rust fungus या नाइट्रोजन की कमी हो सकती है। Mancozeb 75 WP 2.5 ग्राम/लीटर स्प्रे करें या यूरिया 20-25 किग्रा/बीघा डालें।"},
    {"id": 3, "query": "PM किसान सम्मान निधि कैसे मिलेगी", "response": "PM किसान सम्मान निधि में हर साल ₹6000 मिलते हैं — तीन किस्तों में। आधार से लिंक बैंक खाता होना जरूरी है। pmkisan.gov.in पर रजिस्ट्रेशन करें या नजदीकी CSC केंद्र जाएं।"},
    {"id": 4, "query": "फसल बीमा कैसे करें", "response": "PM फसल बीमा योजना के लिए बैंक या CSC केंद्र जाएं। बुवाई के 10 दिन के अंदर करवाएं। खरीफ में 2% और रबी में 1.5% प्रीमियम देना होता है।"},
    {"id": 5, "query": "मिट्टी की जांच कहाँ होगी", "response": "मृदा स्वास्थ्य कार्ड के लिए नजदीकी KVK या कृषि विभाग कार्यालय में जाएं। मिट्टी का सैंपल दें — 15-20 दिन में रिपोर्ट मिल जाएगी। यह मुफ्त है।"},
]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Samadhan Mitra"})


@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """
    Main chat endpoint — single Gemini call architecture.
    Accepts:
      - text: str  (Hindi text query)
      - phone: str  (farmer phone number)
      - audio_b64: str  (optional base64 audio for Groq Whisper STT)
      - image_b64: str  (optional base64 image for crop diagnosis)
    Returns:
      - response: str  (Hindi text response)
      - domain: str  (agriculture|health|schemes|general)
      - transcription: str  (if audio was sent, the transcribed text)
    """
    data = request.get_json(force=True)
    phone = data.get("phone", "unknown")
    text = data.get("text", "")
    audio_b64 = data.get("audio_b64")
    image_b64 = data.get("image_b64")

    transcription = None

    # STT: convert audio to text via Groq Whisper
    if audio_b64 and not text:
        try:
            audio_bytes = base64.b64decode(audio_b64)
            text = groq_transcribe(audio_bytes)
            transcription = text
            if not text:
                return jsonify({"error": "आवाज़ समझ नहीं आई — कृपया दोबारा बोलें"}), 422
        except Exception as e:
            print(f"[STT error] {e}")
            return jsonify({"error": "आवाज़ प्रोसेस नहीं हो पाई"}), 422

    if not text:
        return jsonify({"error": "No query provided"}), 400

    # Load or create farmer profile
    profile = get_or_create_profile(phone)

    # Check session timeout — archive old session if needed
    if check_session_timeout(profile):
        old_messages = profile.get("active_session", {}).get("messages", [])
        if old_messages:
            summary = generate_session_summary(old_messages)
            profile = archive_session(profile, summary)

    # Add user message to session
    profile = add_message(profile, "user", text, has_image=bool(image_b64))

    # Single Gemini call — response + profile update
    result = chat(text, profile, image_b64=image_b64)

    response_text = result["response"]
    domain = result["domain"]
    profile_update = result.get("profile_update")

    # Add assistant message to session
    entities = profile_update.get("entities_extracted", {}) if profile_update else {}
    profile = add_message(profile, "assistant", response_text, domain=domain, entities=entities)

    # Apply profile update from Gemini's structured extraction
    if profile_update:
        profile = apply_profile_update(profile, profile_update)

    # Save profile
    save_profile(phone, profile)

    response = {
        "response": response_text,
        "domain": domain,
    }
    if transcription:
        response["transcription"] = transcription

    return jsonify(response)


@app.route("/greeting", methods=["POST"])
def greeting_endpoint():
    """
    Generate a proactive greeting for the farmer (Layer 4 — Perceived Memory).
    Accepts: { phone: str }
    Returns: { greeting: str }
    """
    data = request.get_json(force=True)
    phone = data.get("phone", "unknown")

    profile = get_or_create_profile(phone)

    # Check session timeout — archive old session if needed
    if check_session_timeout(profile):
        old_messages = profile.get("active_session", {}).get("messages", [])
        if old_messages:
            summary = generate_session_summary(old_messages)
            profile = archive_session(profile, summary)
            save_profile(phone, profile)

    greeting = generate_greeting(profile)

    return jsonify({"greeting": greeting})


@app.route("/profile/<phone>", methods=["GET"])
def profile_endpoint(phone):
    """Partner view: returns farmer profile by phone number."""
    data = get_profile(phone)
    if not data:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(data)


@app.route("/partner/<phone>/summary", methods=["GET"])
def partner_summary_endpoint(phone):
    """Generate AI summary card for the partner view."""
    profile = get_profile(phone)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    summary = generate_partner_summary(profile)
    return jsonify({"summary": summary})


@app.route("/offline", methods=["GET"])
def offline_cache():
    """Returns cached Q&A pairs for offline fallback."""
    return jsonify({"cache": OFFLINE_CACHE})


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5001))
    app.run(debug=True, port=port)
