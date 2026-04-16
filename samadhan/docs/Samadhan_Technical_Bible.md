# SAMADHAN — Complete Project Technical Bible
## Version: Pre-Hackathon Final Architecture (April 2026)
## Hackathon: TinkerQuest 26, IIT Roorkee
## Problem Statement: PS1 — Samadhan with AI – Rural Intelligence Systems

---

## TABLE OF CONTENTS
1. Project Vision & Core Thesis
2. The Problem We're Solving
3. Product Definition — What Samadhan Is
4. User Personas
5. The Three-Domain Scope & Justification
6. Complete Technical Architecture
7. Memory System — Four-Layer Design
8. Knowledge System — Three-Tier Approach
9. Profile Schema — Complete JSON Structure
10. System Prompt Design Principles
11. Partner View — Design & Purpose
12. Voice Pipeline — Complete Flow
13. PWA & Offline Strategy
14. Demo Script — Hackathon Presentation
15. What Is NOT In V1
16. Known Issues & Mitigations
17. Knowledge Base Curation Plan
18. Implementation Checklist & Time Estimates
19. Key Design Decisions Log (With Reasoning)

---

## 1. PROJECT VISION & CORE THESIS

**One-sentence definition:**
Samadhan is a voice-first Hindi conversational assistant for Indian farmers that solves their daily problems across agriculture, health, and government schemes — while invisibly building a structured life profile that enables any service provider (ASHA worker, Krishi officer, FPO agent) to serve them with full context.

**Core thesis:**
In rural India, the farmer interacts with at least three disconnected systems — agriculture, healthcare, and government welfare. None of these systems share context. The ASHA worker doesn't know about his crop loss. The Krishi officer doesn't know about his health crisis. The insurance company doesn't know either. Samadhan is the first place where a farmer's complete rural life exists in one view.

**The innovation is NOT the chatbot.** Every hackathon team can build a chatbot. The innovation is:
1. **Talking is documenting.** Every conversation invisibly builds a timestamped, structured profile. The farmer never fills a form.
2. **The profile enables human connections.** When the ASHA worker opens Ramesh's profile, she sees his full season — crop problems, health queries, scheme status — and can serve him as a whole person, not a ticket number.
3. **The system remembers.** Unlike every other rural chatbot, Samadhan maintains conversational continuity across sessions, references past interactions, and proactively follows up.

---

## 2. THE PROBLEM WE'RE SOLVING

**Primary problem:** Rural farmers in India have no persistent, unified record of their agricultural, health, and welfare interactions. Every interaction with every system starts from zero. This leads to:

- **Crop insurance claims rejected** because farmers can't prove what they planted, when problems started, or what they did about it. PMFBY claims require documentation most farmers don't have.
- **Duplicated effort** by service providers. The ASHA worker asks the same questions the Krishi officer asked last week. The farmer repeats his story to every new person.
- **Missed entitlements.** Farmers don't know about schemes they qualify for. No system connects their profile to available benefits.
- **No follow-up.** If a farmer reports a crop problem and gets advice, nobody checks if it worked. If his wife had a fever last week, nobody asks if she went to the sub-center.

**Secondary problem:** Existing digital solutions fail because they require:
- App downloads (farmers don't have storage or comfort with app stores)
- Form filling (literacy barrier)
- Text input (many farmers are more comfortable with voice)
- Single-domain focus (agriculture OR health OR schemes, never together)

**What success looks like:** A farmer talks to Samadhan naturally over a season. When disaster strikes (crop failure, health emergency, scheme deadline), his entire history is documented and accessible to the people who can help him. His claim has evidence. His ASHA worker has context. His entitlements are tracked.

---

## 3. PRODUCT DEFINITION — WHAT SAMADHAN IS

### What the farmer experiences:
- A chat interface (PWA, installable on home screen) that feels familiar — like WhatsApp.
- He speaks in Hindi (voice note) or types. Samadhan responds in simple Hindi (text + voice).
- He can send photos of crop problems for visual diagnosis.
- Sometimes Samadhan reaches out first — a proactive greeting that references his last conversation, reminds about deadlines, or follows up on an unresolved problem.
- He can scroll back and see previous conversations, even offline.

### What the partner (ASHA worker / Krishi officer / FPO agent) experiences:
- A simple web page. Enter the farmer's phone number or name.
- See a one-page summary: farmer profile, timeline of all interactions, current status across agriculture/health/schemes, flagged concerns, upcoming deadlines.
- An AI-generated summary card that reads like a patient file — one paragraph that gives the partner full context before they visit or interact with the farmer.

### What Samadhan does internally:
- Processes voice to text (Groq Whisper API).
- Sends text + image (if any) + conversation history + profile context to Gemini 2.5 Flash.
- Receives a conversational response AND structured JSON profile update in one API call.
- Updates the farmer's profile with extracted entities (crop, problem, family member, scheme, symptom, etc.).
- Generates session summaries when sessions end.
- Maintains a timeline of all interactions for the partner view.

---

## 4. USER PERSONAS

### Primary User: The Farmer
- **Name (demo):** Ramesh, 54, wheat and sugarcane farmer
- **Location:** Landhaura village, Haridwar district, Uttarakhand
- **Land:** 2 bigha (approx 0.5 acre)
- **Digital comfort:** Uses WhatsApp for voice notes to family. Can make calls. Doesn't type in Hindi easily. Has a basic Android phone with intermittent 4G.
- **Language:** Hindi (Khariboli/Western UP dialect). Some Punjabi influence. No English.
- **Needs:** Crop advice, scheme information, basic health guidance. Doesn't know what he doesn't know — needs proactive information.
- **Trust model:** Trusts people, not technology. Will trust Samadhan if it feels like a knowledgeable neighbor, not a government portal.

### Secondary User: The Partner (ASHA Worker / Krishi Mitra)
- **Name (demo):** Sunita, 32, ASHA worker serving 50 families
- **Digital comfort:** Uses smartphone daily, comfortable with simple web interfaces.
- **Need:** Context before visiting a family. Wants to know what problems they're facing, what advice they've received, what follow-ups are needed. Currently relies on memory and paper registers.
- **Value from Samadhan:** She sees a family's complete recent history in 30 seconds. She can have more informed, efficient, and empathetic interactions.

---

## 5. THE THREE-DOMAIN SCOPE & JUSTIFICATION

### Why three domains, not one:
1. **PS1 requirement:** The problem statement explicitly mentions "agriculture, healthcare, education, or government schemes" and expects a system that "aggregates information from multiple sources."
2. **Profile value multiplier:** A single-domain profile (just crops) is useful but narrow. A multi-domain profile (crops + health + schemes) paints a complete picture of a farmer's life. This is dramatically more valuable for the partner view and for the demo narrative.
3. **Architectural simplicity:** With a single-LLM architecture (no separate agents), adding domains is just adding knowledge to the system prompt — not adding code complexity.
4. **Natural conversation flow:** Farmers don't compartmentalize their lives. "Gehun kharab ho gaya, wife beemar hai, aur PM-Kisan ka paisa nahi aaya" — that's one message touching three domains. A single-domain system would ignore two-thirds of it.

### Domain depth strategy:
- **Agriculture:** DEEP. 10 crops × 5-6 problems each. Specific, verified advice with chemical names and dosages. This is the strongest domain.
- **Schemes:** COMPREHENSIVE. 10 government schemes with eligibility, benefits, process, deadlines, required documents.
- **Health:** DELIBERATELY SHALLOW BUT USEFUL. 8-10 common scenarios. Triage only — acknowledge, give one safe immediate action, state when to seek help, name the facility type, mention Ayushman if relevant. NEVER diagnose. NEVER prescribe medicines.

---

## 6. COMPLETE TECHNICAL ARCHITECTURE

### High-Level Flow:
```
FARMER FLOW:
Voice → Groq Whisper (STT) → Hindi text
                                    ↓
Text + Image (if any) + Last 5-10 messages + Profile context → Gemini 2.5 Flash
                                    ↓
             ┌──────────────────────┴──────────────────────┐
     Conversational Response              Structured JSON
     (shown + spoken to farmer)     (profile update, domain tag,
                                     extracted entities, timeline entry)
             ↓                                    ↓
     Google Cloud TTS / Web Speech      Profile JSON updated
     speaks response in Hindi           (stored per phone number)

PARTNER FLOW:
Enter phone number → Load profile JSON → Render timeline + summary card
                                              ↓
                              Gemini call for intelligent one-para summary
```

### Tech Stack:
| Component | Technology | Why |
|---|---|---|
| Frontend | React (PWA-enabled) | Installable, offline-capable, familiar UI |
| Backend | Flask (Python) | Simple, team knows Python, sufficient for hackathon |
| Speech-to-Text | Groq Whisper Large V3 API (free) | Best free Hindi STT, sub-second latency |
| LLM + Vision | Gemini 2.5 Flash (free tier) | Multimodal (text + image in one call), strong Hindi, 500 req/day free |
| Text-to-Speech | Google Cloud TTS (free tier) / Web Speech API fallback | Hindi WaveNet voice is natural; Web Speech as offline fallback |
| Storage | JSON files per farmer (file system) | No database needed for V1/hackathon |
| Partner View | Same React app, `/partner` route | Shared codebase, simpler deployment |

### Why This Stack (Key Decisions):

**Why Gemini 2.5 Flash over other LLMs:**
- Free tier: 500 requests/day (sufficient for hackathon + testing)
- Multimodal: handles text AND images in one API call (no separate vision API needed for crop photo diagnosis)
- Strong Hindi capability
- Large context window for conversation history
- Chat API natively supports message history

**Why Groq Whisper for STT instead of browser Web Speech API:**
- Browser Web Speech API is inconsistent across devices and doesn't work offline properly
- Groq Whisper Large V3 has significantly better Hindi accent handling
- Free tier, sub-second inference
- More reliable for regional Hindi dialects (Khariboli, Western UP)

**Why NO separate router/agent architecture:**
- Originally designed with 3 separate AI agents (Sunno router → Khet/Sehat/Haq agents) = 2 API calls per message
- Redesigned to single Gemini call with comprehensive system prompt
- Benefits: half the latency, no routing errors, no 64-token truncation bug, simpler codebase
- The LLM IS the router — it handles domain classification internally

**Why JSON files instead of a database:**
- Three-person team, limited time
- JSON is human-readable (easy to debug and demo)
- Profile structure is still evolving
- Can migrate to SQLite/PostgreSQL later
- For hackathon scale (demo with 2-3 farmer profiles), this is more than sufficient

---

## 7. MEMORY SYSTEM — FOUR-LAYER DESIGN

This is the most critical technical design in the project. "Memory" is actually four distinct problems:

### Layer 1 — Conversational Memory (Within a Session)
**Problem:** Farmer says "mere gehun ke patte peele hain." Samadhan responds about rust. Farmer says "iske liye kya spray karein?" Without context, "iske" is meaningless.

**Solution:** Maintain an `active_session.messages` array in the farmer's profile. Send the last 5-10 message pairs to Gemini via its native chat history API.

**Session detection:** If `last_active` timestamp is within 30 minutes, same session — append. If older than 30 minutes, new session — archive old session and start fresh.

**Implementation:**
```python
# Gemini chat API with history
chat = model.start_chat(history=[
    {"role": "user", "parts": [msg["text"]]}
    if msg["role"] == "user" else
    {"role": "model", "parts": [msg["text"]]}
    for msg in active_session_messages
])
response = chat.send_message(new_message)
```

**Cap:** 10 message pairs per session. Beyond that, trim oldest 2.

### Layer 2 — Session Memory (Across Days)
**Problem:** Ramesh talked about wheat rust on Monday. On Thursday he says "woh spray kaam nahi kiya." Active session is empty — it's a new conversation. But he expects Samadhan to remember.

**Solution:** When a session ends (30-minute gap detected), generate a one-line AI summary of that session. Store in `recent_sessions` array. Inject last 3 session summaries into the system prompt context for every new session.

**Summary generation:** One Gemini call at session close:
```
"Summarize this farmer conversation in one Hindi line for future reference: [session messages]"
```

**Stored as:**
```json
"recent_sessions": [
  {
    "date": "2026-04-11",
    "summary": "Reported yellowing in wheat, likely rust. Advised Mancozeb 75 WP spray at 2.5g/L.",
    "domain": "agriculture"
  }
]
```

**Injected into system prompt as:**
```
Previous interactions with this farmer:
- April 11: Reported yellowing in wheat, likely rust. Advised Mancozeb spray.
- April 8: Asked about PM-Kisan installment status.
- April 3: Wife had 2-day fever, directed to sub-center.
```

**Bonus:** These session summaries double as the timeline entries for the partner view. One feature, two uses.

### Layer 3 — Life Memory (Structured Profile)
**Problem:** Over months, accumulated facts about the farmer need to persist: what crops he grows, his family's health queries, which schemes he's enrolled in.

**Solution:** Structured JSON profile extracted from every conversation via the Gemini response. The system prompt instructs Gemini to output a `<profile_update>` JSON block alongside every conversational response.

**Extraction instruction in system prompt:**
```
After every response, output the following JSON inside <profile_update> tags:
{
  "domain": "agriculture|health|schemes|general",
  "entities_extracted": {
    "crop": null or string,
    "problem": null or string,
    "family_member": null or string,
    "scheme_name": null or string,
    "symptom": null or string,
    "action_taken": null or string,
    "location_mentioned": null or string
  },
  "session_summary_update": "one line describing this exchange",
  "flags": ["any alerts like upcoming_deadline, unresolved_problem, emergency"]
}
```

Backend parses this JSON and merges into the persistent profile.

### Layer 4 — Perceived Memory (UX Layer)
**Problem:** Even with perfect backend memory, if the farmer opens the app and sees an empty screen, he feels forgotten.

**Solution A — Chat history display:** PWA caches last 20-30 messages in the browser. When farmer opens app, previous messages are visible (grayed out, labeled "pichhli baat-cheet").

**Solution B — Proactive greeting:** When a new session starts after a gap, Samadhan sends an AI-generated greeting referencing the farmer's recent activity:

"Namaste Ramesh bhai! Pichhli baar aapne gehun mein rust ki baat ki thi. Kya spray se fayda hua? Aur haan — aapki fasal bima ki last date 8 din mein hai."

**Greeting generation:** One Gemini call on session start:
```
"Given this farmer's profile and recent session summaries, generate a warm, brief Hindi greeting that:
1. References their most recent interaction
2. Follows up on any unresolved problem
3. Mentions any upcoming deadline from their profile
Keep it to 2-3 sentences. Speak like a caring neighbor."
```

**This greeting is the single most powerful demo moment.** The chatbot that starts the conversation by showing it already knows you.

### Memory Layers Summary:
| Layer | What It Solves | Implementation | Token Cost |
|---|---|---|---|
| Layer 1: Session History | Follow-ups within a session ("iske liye kya karein?") | Send last 5-10 message pairs via Gemini chat API | Low — only active messages |
| Layer 2: Session Summaries | Cross-session continuity ("woh spray kaam nahi kiya") | AI-generated one-line summary per session, inject last 3 into prompt | Minimal — 3 short lines |
| Layer 3: Profile Facts | Long-term knowledge, partner view, proactive alerts | Structured JSON extracted every exchange | Zero additional — stored locally |
| Layer 4: Perceived Memory | Farmer feels remembered, trust builds | Proactive greeting + cached chat in PWA | One Gemini call on session start |

---

## 8. KNOWLEDGE SYSTEM — THREE-TIER APPROACH

### Why tiers instead of "expand everything" or "say I don't know":
- Blind expansion without verification leads to hallucination (Gemini confidently gives wrong dosages or nonexistent schemes)
- "I don't know" makes the system feel useless and damages farmer trust
- Tiered approach: confident where verified, helpful where general, redirective where out of scope

### Tier 1 — Full Confidence (Verified Knowledge Base)
Content that has been hand-verified against government/ICAR/KVK sources. Samadhan speaks with authority — specific chemical names, dosages, scheme eligibility criteria, deadlines.

**Agriculture (10 crops × 5-6 problems each = 50-60 entries):**
Target crops for Uttarakhand/Western UP: Wheat, Rice, Sugarcane, Potato, Tomato, Peas, Lentils (Masoor), Mustard (Sarson), Soybean, Maize.

For each crop, cover: 2-3 common diseases/pests, 1-2 nutrient deficiency symptoms, 1 irrigation/weather issue. Include: problem identification, recommended treatment (specific chemical + dosage), preventive measures, when to escalate to KVK.

**Schemes (10 schemes with full details):**
PM-Kisan, PMFBY (crop insurance), Ayushman Bharat, Kisan Credit Card, Soil Health Card, PM Fasal Bima Yojana, MGNREGA, Ujjwala Yojana, PM Awas Yojana, Ration Card / PDS.

For each: eligibility criteria, benefit amount/type, application process, required documents, key deadlines, helpline numbers.

**Health (8-10 triage scenarios):**
Fever (2+ days), Child diarrhea, Pregnancy-related concerns, Chest pain (emergency), Skin issues (farming-related), Animal/snake bite, Injury/wound, Eye problems, Breathing difficulty, Child vaccination queries.

For each: acknowledgment, one safe immediate action (ORS, clean wound, rest), clear threshold for seeking help, type of facility to visit, Ayushman relevance. NEVER a diagnosis. NEVER a medicine name.

### Tier 2 — Guided General Knowledge
For queries within agriculture/health/schemes but outside Tier 1 verified content. Gemini uses its training data with strict guardrails.

**System prompt instruction:**
```
For topics NOT in the VERIFIED KNOWLEDGE section:
- Provide general guidance and possible causes
- NEVER give specific chemical names, dosages, or medicine names
- ALWAYS prefix with "yeh meri aam samajh hai, apne Krishi Kendra/doctor se zaroor confirm karein"
- Offer to help further if they send a photo
- Provide the relevant referral (KVK number, sub-center location, etc.)
```

**Example Tier 2 response:**
"Bajra mein patte peele hona kai karanon se ho sakta hai — paani ki kami, nitrogen ki kami, ya koi keeda. Ek photo bhejiye toh aur sahi bata sakta hoon. Aur apne nezdiki Krishi Vigyan Kendra mein bhi zaroor puch lein."

### Tier 3 — Hard Redirect
For topics completely outside scope — legal disputes, land records, police matters, financial investment, etc.

**Response pattern:** Warm acknowledgment + specific redirect with contact information.
"Yeh mere expertise se bahar hai, lekin aapke Block Development Officer isse help kar sakte hain. Unka office [location] mein hai."

### Referral Map (Critical for Tier 2 and 3):
Pre-loaded for Roorkee-Haridwar region:
- Krishi Vigyan Kendra (KVK) Roorkee — address, phone, hours
- Nearest sub-centers and PHCs — 3-4 locations
- District Hospital Haridwar — address, emergency number
- Common Service Centres (CSC) — 2-3 locations
- Block Development Office — address, phone
- Ambulance: 108
- ASHA worker helpline (if available)
- PM-Kisan helpline: 155261
- Ayushman helpline: 14555

This referral map turns every "out of scope" moment into a "here's exactly who can help" moment.

---

## 9. PROFILE SCHEMA — COMPLETE JSON STRUCTURE

```json
{
  "phone": "9876543210",
  "name": "Ramesh",
  "village": "Landhaura",
  "block": "Roorkee",
  "district": "Haridwar",
  "registered_date": "2026-01-15",

  "active_session": {
    "session_id": "sess_20260414_1030",
    "session_start": "2026-04-14T10:30:00",
    "last_active": "2026-04-14T10:45:00",
    "messages": [
      {
        "role": "user",
        "text": "mere gehun ke patte peele pad rahe hain",
        "timestamp": "2026-04-14T10:30:00",
        "has_image": false
      },
      {
        "role": "assistant",
        "text": "Ramesh bhai, gehun mein patte peele hona aksar rust fungus ki nishani hai...",
        "timestamp": "2026-04-14T10:30:05",
        "domain": "agriculture"
      },
      {
        "role": "user",
        "text": "iske liye kya spray karun?",
        "timestamp": "2026-04-14T10:32:00",
        "has_image": false
      }
    ]
  },

  "recent_sessions": [
    {
      "session_id": "sess_20260411_0900",
      "date": "2026-04-11",
      "summary": "Reported yellowing in wheat, likely rust. Advised Mancozeb 75 WP spray at 2.5g/L.",
      "domain": "agriculture",
      "key_entities": {"crop": "wheat", "problem": "rust_fungus", "treatment": "mancozeb"}
    },
    {
      "session_id": "sess_20260408_1400",
      "date": "2026-04-08",
      "summary": "Wife had fever for 2 days. Directed to Roorkee sub-center. Mentioned Ayushman eligibility.",
      "domain": "health",
      "key_entities": {"family_member": "wife", "symptom": "fever", "referral": "sub-center"}
    },
    {
      "session_id": "sess_20260403_1100",
      "date": "2026-04-03",
      "summary": "Asked about PM-Kisan installment status. Guided to check via mobile number on PM-Kisan portal.",
      "domain": "schemes",
      "key_entities": {"scheme": "pm_kisan", "query": "installment_status"}
    }
  ],

  "profile": {
    "agriculture": {
      "primary_crops": ["wheat", "sugarcane"],
      "land_area": "2 bigha",
      "current_season": "rabi",
      "reported_problems": [
        {
          "date": "2026-04-11",
          "crop": "wheat",
          "problem": "rust_fungus",
          "symptom_described": "yellowing leaves",
          "advice_given": "Mancozeb 75 WP at 2.5g/L",
          "status": "advised_treatment",
          "follow_up_needed": true
        }
      ]
    },
    "health": {
      "family_queries": [
        {
          "date": "2026-04-08",
          "member": "wife",
          "symptom": "fever_2_days",
          "action": "directed_to_subcenter",
          "ayushman_mentioned": true,
          "follow_up_needed": true
        }
      ]
    },
    "schemes": {
      "pm_kisan": {"status": "active", "last_checked": "2026-04-03"},
      "pmfby": {"status": "unknown", "deadline_approaching": true, "deadline_date": "2026-04-22"},
      "ayushman": {"status": "likely_eligible", "card_status": "unknown"},
      "kcc": {"status": "unknown"},
      "ration_card": {"status": "unknown"}
    }
  },

  "flags": [
    "crop_problem_unresolved_wheat_rust",
    "insurance_deadline_8_days",
    "health_follow_up_needed_wife_fever"
  ],

  "timeline": [
    {
      "date": "2026-04-11",
      "domain": "agriculture",
      "summary": "Reported wheat rust, advised Mancozeb spray",
      "status": "unresolved"
    },
    {
      "date": "2026-04-08",
      "domain": "health",
      "summary": "Wife fever, directed to sub-center",
      "status": "follow_up_needed"
    },
    {
      "date": "2026-04-03",
      "domain": "schemes",
      "summary": "PM-Kisan status check",
      "status": "resolved"
    }
  ]
}
```

---

## 10. SYSTEM PROMPT DESIGN PRINCIPLES

The system prompt is the single most important engineering artifact. It must accomplish ALL of the following in ONE Gemini API call:
1. Respond conversationally in simple Hindi
2. Handle multi-domain queries naturally
3. Extract structured profile data as JSON
4. Respect knowledge tier boundaries
5. Use conversation history for follow-ups
6. Feel warm, trustworthy, and human

### Prompt Structure (Sections):

**Section 1 — Identity & Personality:**
- Name: Samadhan Mitra
- Speaks simple, warm Hindi (Khariboli)
- Tone: caring neighbor, not government officer or doctor
- Conservative with advice — always suggests confirming with local expert
- Never diagnoses medically, never guarantees scheme eligibility
- Uses farmer's name when known
- Keeps responses short (2-4 sentences for simple queries, max 5-6 for complex)

**Section 2 — Knowledge Tier Instructions:**
- Tier 1 verified knowledge: respond with confidence and specifics
- Tier 2 general knowledge: provide guidance with explicit disclaimer, no specific chemicals/medicines/dosages, offer photo upload, provide referral
- Tier 3 out of scope: warm redirect with specific contact info
- NEVER fabricate information. NEVER make up scheme names, chemical names, or dosages.

**Section 3 — Verified Knowledge Blocks:**
- [Agriculture knowledge base — all Tier 1 crop entries]
- [Schemes knowledge base — all Tier 1 scheme entries]
- [Health triage scenarios — all Tier 1 entries]
- [Referral map — KVK, sub-centers, CSCs, helplines]

**Section 4 — Profile Extraction:**
- After every response, output structured JSON inside `<profile_update>` tags
- JSON format specified (see Section 9 above)
- Only include fields actually mentioned in conversation
- This JSON must NEVER appear in the user-facing response

**Section 5 — Conversation History Instructions:**
- Previous messages are provided as chat history
- Use them to resolve pronouns ("iske," "woh," "us")
- If a follow-up references something from a previous session, session summaries are injected in the context
- Maintain topic continuity unless the farmer explicitly changes subject

**Section 6 — Multi-Topic Handling:**
- If the farmer mentions multiple domains in one message, address each naturally
- Order: address them in the sequence the farmer mentioned them
- Each domain response should be 1-2 sentences, connected naturally

**Section 7 — Proactive Behavior (when generating greetings):**
- Reference the most recent unresolved issue
- Mention any upcoming deadlines from profile
- Ask about follow-up on previous advice
- Keep to 2-3 sentences maximum
- Sound like a friend checking in, not a system sending notifications

---

## 11. PARTNER VIEW — DESIGN & PURPOSE

### Who uses it:
ASHA workers, Krishi Mitras, FPO agents, block-level officers. Anyone who serves the farmer and needs context.

### Interface (V1 — minimal):
- Single page, accessible at `/partner` route
- One input field: phone number or farmer name
- Output: farmer profile rendered as a readable page

### Layout:
**Top bar:** Farmer name, village, phone, last active date

**Left/main column — Timeline:**
- Reverse-chronological list of all interactions
- Each entry: date, domain color tag (green=agriculture, blue=health, orange=schemes), one-line summary, status badge (resolved/unresolved/follow-up needed)
- Scrollable, last 3 months of activity

**Right column / top card — AI Summary:**
- Auto-generated one-paragraph summary via Gemini
- Prompt: "Given this farmer's profile and timeline, generate a one-paragraph summary in simple Hindi that an ASHA worker would find useful before visiting the family."
- Example output: "Ramesh, Landhaura, gehun aur ganna kisan. Pichle mahine gehun mein rust ki shikayat thi, Mancozeb spray bataya gaya lekin follow-up nahi hua. Patni ko bukhar tha, sub-center bheja gaya. PM-Kisan active hai. Fasal bima ki deadline 8 din mein hai — registration confirm nahi hua."

**Bottom section — Quick Facts:**
- Current crops | Land area
- Active schemes | Pending applications
- Recent health queries
- Flagged concerns (in red)

### Technical implementation:
- Same React app, different route
- Reads from the same farmer JSON profiles
- One Gemini call for the AI summary on profile load
- No authentication in V1 (hackathon scope)

---

## 12. VOICE PIPELINE — COMPLETE FLOW

### Farmer speaks → Response spoken back (full round trip):

```
Step 1: Farmer taps mic button in PWA, speaks in Hindi
Step 2: Browser MediaRecorder captures audio as WebM/WAV
Step 3: Audio blob sent to Flask backend via POST /api/voice
Step 4: Backend sends audio to Groq Whisper API
        → Returns Hindi text transcription
Step 5: Backend retrieves farmer profile (by phone number from session)
Step 6: Backend constructs Gemini API call:
        - System prompt (with knowledge base)
        - Injected context: last 3 session summaries + profile summary
        - Chat history: active session messages
        - New message: transcribed text + image (if attached)
Step 7: Gemini returns:
        - Conversational Hindi response (for the farmer)
        - <profile_update> JSON block (for the backend)
Step 8: Backend parses response:
        - Extracts conversational text → sends to frontend
        - Extracts JSON → updates farmer profile
        - Appends exchange to active_session.messages
Step 9: Frontend displays text response
Step 10: Frontend sends text to Google Cloud TTS API (or Web Speech API fallback)
         → Plays Hindi audio response
Step 11: Farmer hears the response and sees the text
```

### Latency budget (target: under 4 seconds total):
| Step | Estimated Time |
|---|---|
| Audio capture + upload | ~500ms |
| Groq Whisper STT | ~800ms |
| Gemini processing | ~1500ms |
| Google TTS | ~500ms |
| Network overhead | ~500ms |
| **Total** | **~3.5-4 seconds** |

### Fallback handling:
- If Groq is down: fall back to browser Web Speech API for STT (lower quality Hindi but functional)
- If Google TTS is down: fall back to browser Web Speech API for TTS
- If Gemini is down: show cached "service unavailable" message in Hindi, offer to queue the message

---

## 13. PWA & OFFLINE STRATEGY

### PWA Implementation:
- `manifest.json` with app name "Samadhan Mitra", theme colors, icons
- Service worker for:
  - Caching app shell (HTML, CSS, JS) — works offline
  - Caching last 20-30 conversations in browser storage (IndexedDB or Cache API)
  - Message queue for offline voice notes (Background Sync API)

### Offline capabilities:
1. **Read previous conversations:** Farmer can scroll back and re-read previous advice even with zero signal
2. **Queue messages:** Farmer records a voice note offline → stored locally → auto-sends when signal returns
3. **App access:** PWA shell loads from cache, farmer sees the interface even without internet

### What does NOT work offline:
- New AI responses (requires Gemini API)
- Voice-to-text (requires Groq API)
- Photo analysis (requires Gemini vision)
- Partner view (requires loading profile from backend)

### Demo talking point:
"Samadhan works even when the farmer has no signal. His message waits and sends automatically when connectivity returns. And he can always scroll back to read previous advice — even in the field with zero bars."

---

## 14. DEMO SCRIPT — HACKATHON PRESENTATION

### Setup:
- PWA open on a phone-sized screen (or actual phone mirrored)
- Partner view open on a laptop
- Ramesh's profile pre-populated with 4-5 session summaries showing a season's progression

### Scene 1 — The Greeting (Perceived Memory)
Ramesh opens Samadhan after a 3-day gap.
Samadhan greets: "Namaste Ramesh bhai! Pichhli baar aapne gehun mein rust ki baat ki thi. Kya spray se fayda hua? Aur haan — aapki fasal bima ki last date 8 din mein hai."

**What judges see:** The system remembers. It follows up. It proactively alerts about a deadline.

### Scene 2 — Multi-Domain Message (Core Capability)
Ramesh sends a voice note: "Spray se thoda fayda hua lekin poora nahi. Aur meri wife ko phir se bukhar aa gaya hai. PM-Kisan ka paisa bhi nahi aaya."

Samadhan responds addressing all three:
- Agriculture: follow-up advice on rust treatment (re-spray after 10 days)
- Health: wife's recurring fever — advises sub-center visit, mentions Ayushman
- Schemes: PM-Kisan status check guidance

**What judges see:** One message, three domains, handled naturally. No routing confusion.

### Scene 3 — Photo Diagnosis (Vision Capability)
Ramesh sends a photo of his wheat leaves with spots.
Samadhan analyzes the image and responds with a specific diagnosis and treatment.

**What judges see:** Multimodal capability. Farmer doesn't need to describe the problem perfectly — the photo speaks.

### Scene 4 — The Partner View (The Demo Closer)
ASHA worker Sunita opens the partner view. Types Ramesh's phone number.
She sees: his full timeline (rust problem, wife's fever, PM-Kisan query, insurance deadline), AI-generated summary card, all flags.
She now knows everything about this family before her visit.

**What judges see:** The invisible profile. The complete rural life record. The human connection enabled by technology. This is the "gasp" moment.

### Pitch closer:
"Every farmer in India interacts with agriculture, healthcare, and government schemes. None of these systems talk to each other. Samadhan is the first place where a farmer's complete rural life exists in one view — built from nothing but natural conversation."

---

## 15. WHAT IS NOT IN V1

Explicitly excluded from hackathon scope:
- Real WhatsApp Business API integration (simulated in PWA)
- Aadhaar linkage or identity verification
- Blockchain anything
- Complex analytics or dashboards
- Multi-language beyond Hindi
- Real-time scheme database scraping
- Actual insurance claim filing
- Payment or transaction layer
- Machinery marketplace or e-commerce
- Complex access control for partner view
- Education domain (mentioned in PS but deprioritized)
- Real SMS/notification system
- Multiple partner role types (all partners see same view in V1)

All of these are valid V2/V3 features. V1 proves the core thesis: farmer talks, profile builds, partner gets context.

---

## 16. KNOWN ISSUES & MITIGATIONS

| Issue | Risk | Mitigation |
|---|---|---|
| Hindi STT accuracy for regional accents | Medium | Test with actual Haridwar-accent Hindi samples; Groq Whisper is best available free option |
| Gemini hallucination on unverified topics | High | Three-tier knowledge system; strict system prompt guardrails; Tier 2 never gives specific chemicals |
| Free API rate limits (Gemini 500/day) | Low for hackathon | Sufficient for demo; cache responses for repeated queries during testing |
| TTS Hindi voice quality | Medium | Google Cloud TTS WaveNet for demo; Web Speech API as fallback |
| Profile JSON parsing failures | Medium | Validate JSON structure in backend; fallback to "no profile update" if parsing fails (don't crash) |
| Multi-topic message handling | Medium | Explicit system prompt instructions + 3-4 example messages in prompt for N-shot learning |
| Session boundary detection | Low | 30-minute timeout is simple and reliable |
| Image upload on slow connections | Medium | Compress image client-side before upload; show progress indicator; timeout gracefully |

---

## 17. KNOWLEDGE BASE CURATION PLAN

### Agriculture (Target: 10 crops × 5-6 problems = ~55 entries)
**Method:** Use Gemini to draft entries → verify against ICAR/KVK/state agriculture department sources → finalize.

**Format per entry:**
```json
{
  "crop": "wheat",
  "problem": "rust_fungus",
  "local_names": ["geeri", "rust"],
  "symptoms": "Leaves develop orange-brown pustules, usually on the underside. Yellowing of affected leaves.",
  "causes": "Fungal infection (Puccinia species), spreads in humid conditions, 15-25°C temperature range.",
  "treatment": "Spray Mancozeb 75 WP at 2.5g per litre of water. Repeat after 10-15 days if needed. Propiconazole 25 EC at 1ml/litre for severe cases.",
  "prevention": "Use resistant varieties (HD-2967, PBW-550). Avoid late sowing. Ensure proper spacing.",
  "escalation": "If more than 30% leaves affected, consult KVK immediately.",
  "source": "ICAR-IIWBR Karnal advisory"
}
```

**Work split:** 3 team members × 3-4 crops each × 2-3 hours = one day.

### Schemes (Target: 10 schemes)
**Method:** Direct from official government websites (pmkisan.gov.in, pmfby.gov.in, pmjay.gov.in, etc.)

**Format per scheme:**
```json
{
  "scheme": "PM-KISAN",
  "full_name": "Pradhan Mantri Kisan Samman Nidhi",
  "benefit": "₹6,000 per year in 3 installments of ₹2,000",
  "eligibility": "All landholding farmer families with cultivable land",
  "exclusions": "Income tax payers, government employees, institutional landholders",
  "documents_needed": ["Aadhaar card", "Bank account", "Land records"],
  "how_to_apply": "Through local Patwari/Lekhpal, CSC centre, or online at pmkisan.gov.in",
  "helpline": "155261 or 011-24300606",
  "key_dates": "Installments usually in April, August, December",
  "check_status": "pmkisan.gov.in → Farmer Corner → Beneficiary Status"
}
```

**Work split:** 1 person × 3-4 hours.

### Health (Target: 8-10 triage scenarios)
**Format per scenario:**
```json
{
  "scenario": "fever_over_2_days",
  "symptoms_described": ["bukhar", "tez bukhar", "badan garam"],
  "immediate_advice": "Paani zyada piyein. Paracetamol le sakte hain agar dard ho. Aram karein.",
  "seek_help_when": "2 din se zyada bukhar ho, ya tez thand lag rahi ho, ya ulti/dast bhi ho",
  "where_to_go": "Nearest sub-center or PHC",
  "ayushman_relevant": true,
  "emergency_signs": ["105°F se zyada bukhar", "behoshi", "body par rash/daane"],
  "NEVER_do": "Never name a specific medicine other than basic paracetamol/ORS. Never diagnose malaria/dengue/typhoid."
}
```

**Work split:** 1 person × 1-2 hours. Keep it deliberately simple.

### Referral Map (Target: 15-20 entries for Roorkee-Haridwar)
Research and compile: KVK address/phone, 3-4 sub-centers/PHCs, district hospital, 2-3 CSCs, BDO office, helpline numbers. 1 person × 1 hour.

---

## 18. IMPLEMENTATION CHECKLIST & TIME ESTIMATES

### Phase 1 — Core Backend (Day 1, ~6-8 hours)
- [ ] Flask app setup with single `/api/chat` endpoint
- [ ] Groq Whisper integration for STT
- [ ] Gemini 2.5 Flash integration (single call, chat history support)
- [ ] System prompt V1 (identity + Tier instructions + one crop knowledge block for testing)
- [ ] Profile JSON read/write (file-based, keyed by phone number)
- [ ] Session management (30-min timeout, active session messages, archival)
- [ ] Profile update JSON parsing from Gemini response
- [ ] Session summary generation on session close

### Phase 2 — Frontend Farmer View (Day 1-2, ~5-6 hours)
- [ ] React app scaffolding (chat interface, WhatsApp-like design)
- [ ] Voice recording + upload to backend
- [ ] Text input alternative
- [ ] Image upload (camera capture for crop photos)
- [ ] Response display (text + TTS playback)
- [ ] Loading states ("Samadhan soch raha hai...")
- [ ] Previous message display from cache
- [ ] Proactive greeting on session start

### Phase 3 — Knowledge Base (Day 2, ~6-8 hours split across team)
- [ ] Agriculture: 10 crops × 5-6 problems each (curated + verified)
- [ ] Schemes: 10 schemes with complete details
- [ ] Health: 8-10 triage scenarios
- [ ] Referral map: 15-20 local contacts
- [ ] Integrate all knowledge into system prompt
- [ ] Test system prompt with 20+ varied queries

### Phase 4 — Partner View (Day 2-3, ~4-5 hours)
- [ ] `/partner` route in React app
- [ ] Phone number input → profile load
- [ ] Timeline rendering (color-coded, chronological)
- [ ] AI summary card generation
- [ ] Quick facts sidebar
- [ ] Flags display

### Phase 5 — PWA + Polish (Day 3, ~3-4 hours)
- [ ] manifest.json + service worker setup
- [ ] Offline shell caching
- [ ] Conversation caching in browser
- [ ] Message queue for offline voice notes
- [ ] Google Cloud TTS integration for demo
- [ ] Pre-populate Ramesh's demo profile with realistic session history
- [ ] End-to-end demo run-through (3+ times)

### Phase 6 — Demo Preparation (Day 3, ~2-3 hours)
- [ ] Script the 4-scene demo flow
- [ ] Pre-record backup voice notes in case live mic fails
- [ ] Prepare 2-minute pitch narrative
- [ ] Test on actual phone (not just laptop)
- [ ] Have fallback plan if any API is down during demo

---

## 19. KEY DESIGN DECISIONS LOG (WITH REASONING)

| Decision | Chosen | Rejected | Reasoning |
|---|---|---|---|
| Number of domains | 3 (agriculture, health, schemes) | 1 (agriculture only) | PS1 requires multi-domain; profile value multiplies with domains; architecturally no extra code cost |
| Agent architecture | Single LLM call, no router | 3 separate agents + Sunno router | Half the latency, no routing bugs, simpler codebase, LLM handles routing internally |
| LLM choice | Gemini 2.5 Flash | Claude API, GPT-4, Groq LLaMA | Free tier sufficient, multimodal (text+vision in one call), strong Hindi, chat history API |
| STT choice | Groq Whisper Large V3 | Browser Web Speech API | Better Hindi accuracy, handles regional accents, free, fast |
| TTS choice | Google Cloud TTS (primary) + Web Speech API (fallback) | Web Speech API only | Google TTS Hindi WaveNet voice is dramatically more natural; critical for demo impact |
| Storage | JSON files per farmer | SQLite, PostgreSQL, Firebase | Simplest for 3-person hackathon team; human-readable for debugging; sufficient for demo scale |
| Knowledge approach | Three-tier (verified + guided + redirect) | "I don't know" for everything unverified / Expand everything without guardrails | Balances coverage with safety; farmer always gets something useful; no hallucination on specifics |
| Memory approach | Four-layer (session + summaries + profile + perceived) | Simple last-5-messages only | Each layer solves a different problem; summaries are token-efficient; perceived memory is the demo wow moment |
| Frontend | PWA (React) | Native app / Actual WhatsApp API | PWA is installable, works offline, no app store; WhatsApp API is complex and costly |
| Offline strategy | Cache conversations + queue messages | Local vector store (flexsearch + IndexedDB) | Queue + cache covers real farmer needs; vector store is over-engineering for V1 |
| Partner view | Timeline + AI summary card | Dashboard with charts / Separate tabs per domain | Timeline tells a story; AI summary is the highest-value feature; avoids dashboard complexity |
| Profile extraction | Gemini outputs JSON alongside response | Separate NLP pipeline / Manual extraction | Single call, no extra infrastructure, JSON is parseable and mergeable |

---

## END OF DOCUMENT

This document is the complete technical bible for Samadhan V1. Any AI assistant receiving this document should have full context to help with: system prompt writing, code implementation, knowledge base creation, UI design, demo scripting, or architectural decisions.

**Key contacts:**
- Team: 3 members, IIT Roorkee, Department of Mechanical & Industrial Engineering
- Hackathon: TinkerQuest 26
- Target region: Roorkee-Haridwar, Uttarakhand
- Primary language: Hindi (Khariboli / Western UP dialect)
- Budget: Zero (free APIs only)
