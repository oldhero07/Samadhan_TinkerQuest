# Samadhan Mitra — AI Farmer Assistant

> **Bringing professional agricultural, health, and subsidy guidance to Indian farmers in their language, at their pace.**

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Core Innovation](#core-innovation)
3. [Problem Statement](#problem-statement)
4. [Design Philosophy](#design-philosophy-frugal-innovation)
5. [Solution](#solution)
6. [Key Features](#key-features)
7. [Tech Stack](#tech-stack)
8. [System Architecture](#system-architecture)
9. [Why This Architecture](#why-this-architecture)
10. [Database Schema](#database-schema)
11. [API Endpoints](#api-endpoints)
12. [Knowledge Base](#knowledge-base)
13. [Configuration](#configuration)
14. [Security Considerations](#security-considerations)
15. [Performance Optimizations](#performance-optimizations)
16. [Future Roadmap](#future-roadmap)
17. [Setup & Deployment](#setup--deployment)
18. [Contributing](#contributing)

---

## Project Overview

**Samadhan Mitra** is an AI-powered farmer assistant built to provide real-time guidance on:
- **Agriculture**: Crop diseases, pest management, best practices (ICAR-verified)
- **Health**: Occupational health, seasonal illnesses, emergency triage
- **Government Schemes**: Subsidy eligibility, application process, key dates
- **Language**: Full Hindi (Devanagari) support for accessibility

The platform uses **Google Gemini AI** to understand farmer queries and provide verified, actionable advice within 10 seconds, with **district-aware referrals** to local agricultural centers, hospitals, and government offices.

### Target Users
- Small and marginal farmers (UP, Uttarakhand)
- ASHA/Anganwadi workers (partner view for farmer summaries)
- Agricultural extension workers

---

## Core Innovation

**Samadhan is NOT just another agricultural chatbot.** The innovation is threefold:

### 1. **Talking is Documenting**
Every conversation invisibly builds a **timestamped, structured farmer profile**. The farmer never fills a form. His questions about wheat rust, his wife's fever, his PM-Kisan status — all automatically become a persistent record that didn't exist before.

### 2. **The Profile Enables Human Connection**
When an ASHA worker opens a farmer's profile before a home visit, she sees his **complete recent history** — crop problems, health queries, scheme status, unresolved flags. She serves him as a whole person, not a ticket number.

### 3. **Evidence from Conversation**
A farmer with 6 months of Samadhan interactions has a **documented crop season** — what he planted, when problems started, what treatment he tried. That's an evidence trail for crop insurance claims (PMFBY) that no paper form captures.

**Result:** Samadhan transforms conversational data into actionable farmer intelligence, enabling better intervention by ASHA workers and better claims outcomes for farmers.

---

## Problem Statement

Indian farmers face critical gaps in accessing timely, trustworthy information:

| Challenge | Current State | Samadhan Solution |
|-----------|---------------|-------------------|
| **Language barrier** | Government resources in English/Hindi mix | 100% Hindi (Devanagari) interface |
| **Information reliability** | Fragmented advice from varied sources | ICAR-verified knowledge base (86 entries) |
| **Accessibility** | Requires literacy, literacy + time | Voice input (Groq Whisper STT), quick response |
| **Geographic relevance** | Generic guidance doesn't fit local context | District-aware referrals (5+ districts mapped) |
| **Subsidy awareness** | Low knowledge of schemes | 15 government schemes explained, eligibility criteria |
| **Health triage** | Over-reliance on local quacks | Structured health scenarios, when to seek help |
| **Real-time support** | Agricultural officers unavailable off-hours | 24/7 AI assistant, <10 second response |

---

## Design Philosophy: Frugal Innovation

Three constraints drove every design decision:

1. **Minimal Digital Literacy** 
 If it requires reading instructions or navigating menus, it fails. The interface is just *conversation* — voice or text. No forms, no navigation, no settings.

2. **Unreliable Connectivity** 
 Rural Uttarakhand has patchy signal. The system:
 - Caches 15 common Q&A offline
 - Queues messages for auto-send when signal returns
 - Stores sessions locally (sessionStorage) before uploading

3. **Zero Cost to Farmer** 
 No subscription, no premium tier, no data charges beyond existing mobile plan. All APIs used are on free-tier (Gemini 1500 RPD, Groq Whisper, etc.). Sustainable by government adoption or NGO funding, not by farmer payments.

**Result:** A system that works in rural India with its real constraints, not an urban-tech fantasy.

---

## Solution

Samadhan Mitra is a **4-tier knowledge system** powered by Google Gemini AI:

```
Farmer Query (voice/text)
 ↓
Groq Whisper (STT) / Text Input
 ↓
Gemini 2.5 Flash AI
 ├─ Tier 1: ICAR-verified knowledge (specific advice with dosages/schemes)
 ├─ Tier 2: General knowledge (caution + referral to KVK/doctor)
 ├─ Tier 3: Out-of-scope (warm redirect to appropriate authority)
 └─ Tier 4: Conversational fallback
 ↓
Profile Update & Timeline Tracking
 ↓
District-Aware Referral Selection
 ↓
Hindi Response + Profile Extraction (JSON)
 ↓
Database Persistence
 ↓
ASHA Partner View (summary + flags)
```

---

## Key Features

### For Farmers (Citizen Interface)

| Feature | Details |
|---------|---------|
| **Voice Input** | 60-second audio recording; Groq Whisper transcription to Hindi |
| **Text Query** | Type in Hindi or English; auto-translated context |
| **Image Analysis** | Crop photo upload for disease diagnosis (Gemini vision) |
| **Onboarding** | Name + district capture (optional, can skip) → personalized responses |
| **Chat History** | Sessions persist for 30 min; max 20 messages per session |
| **Connection Status** | Real-time health indicator (green=ok, orange=slow, red=offline) |
| **Retry Logic** | Failed messages show "दोबारा कोशिश करें" button |
| **Language** | Full Hindi UI (nav, buttons, placeholders, error messages) |
| **Rate Limiting** | 30 requests/min, 200/day (prevents abuse) |
| **Offline Mode** | 15 pre-cached Q&A for no-connectivity scenarios |

### For ASHA/Partner Workers

| Feature | Details |
|---------|---------|
| **Farmer Profile Lookup** | Phone number → full conversation history, flags, timeline |
| **Farmer Flagging** | Mark as: emergency, follow_up_needed, upcoming_deadline, resolved |
| **AI-Generated Summary** | One-paragraph Hindi summary of farmer's situation (for home visits) |
| **Activity Timeline** | Date, domain, status of each interaction |
| **Auth Token** | X-Partner-Token header validation (secure endpoint access) |

### Technical Features

| Feature | Implementation |
|---------|----------------|
| **Multi-Domain Classification** | AI auto-detects: agriculture / health / schemes / general |
| **Profile Extraction** | Structured JSON of entities: crop, problem, scheme, family member, location |
| **Knowledge Caching** | Load JSON files once at startup (not per-call) |
| **Model Cascade** | Try gemini-2.5-flash (1500 RPD), fallback to gemini-2.5-flash-lite on quota |
| **Seasonal Context** | Inject खरीफ (June-Aug) / रबी (Nov-Dec) hints into AI prompt |
| **District Mapping** | 5 districts (Haridwar, Dehradun, Saharanpur, Meerut, Muzaffarnagar) + generic |
| **CORS + Rate Limiting** | Flask-CORS (localhost:5173), Flask-Limiter (memory-based) |
| **Error Handling** | Graceful fallback messages for quota/timeout/network errors |
| **Structured Logging** | ISO timestamps, domains, response lengths, error traces |

---

## Tech Stack

### Backend
```
Language: Python 3.11
Framework: Flask 3.0+
Database: SQLite 3 (SQLAlchemy ORM optional)
AI/LLM: Google Gemini API (2.5-flash)
Speech-to-Text: Groq Whisper API (Hindi support)
CORS: Flask-CORS
Rate Limiting: Flask-Limiter (in-memory)
ENV Config: python-dotenv
Image Proc: Pillow 10.0+
HTTP Client: requests 2.31+
Web Server: Gunicorn (production WSGI)
```

### Frontend
```
Framework: React 18 + Vite 5
Language: JavaScript (ES2020+)
Styling: Inline CSS (no external CSS framework)
Build Tool: Vite (dev: 5173, prod: nginx)
State: sessionStorage (guest_TIMESTAMP format)
HTTP Client: Fetch API
Audio: Web Audio API (60-sec max, format: OGG/WAV)
Error Bound: React ErrorBoundary component
```

### Infrastructure
```
Container: Docker (multi-stage builds)
Orchestration: Docker Compose v3.9
Reverse Proxy: Nginx 1.25 (Alpine)
Port Mapping: Backend 5001 → Flask, Frontend 80 → Nginx
Health Check: GET /health (curl, 30s interval, 3 retries)
DB Backup: Manual weekly backups (samadhan.db.bak.YYYYMMDD)
Logs: Structured logging (ISO format, levelname, message)
```

### APIs & Services
- **Google Gemini API**: LLM (agriculture, health, schemes, entity extraction)
- **Groq Whisper API**: STT (Hindi + English transcription)
- **Google Cloud Storage** (optional): Batch knowledge updates

---

## System Architecture

### High-Level Flow

```
┌──────────────────┐
│ Farmer's Phone │
│ (Browser/App) │
└────────┬─────────┘
 │
 │ Voice/Text/Image
 ↓
┌─────────────────────────┐
│ Frontend (React) │
│ - Onboarding modal │
│ - Chat UI │
│ - Status indicator │
│ - Audio recording │
└────────┬────────────────┘
 │
 │ JSON (district, text, audio_b64, image_b64)
 ↓
┌──────────────────────────────────┐
│ Nginx Reverse Proxy (Port 80) │
│ - /api/* → http://backend:5001/ │
│ - /* → /index.html (SPA) │
└────────┬───────────────────────────┘
 │
 │ HTTP POST /chat, /greeting, /partner/*
 ↓
┌─────────────────────────────────────────────┐
│ Flask Backend (Port 5001) │
│ │
│ ┌─────────────────────────────────────┐ │
│ │ Routes: │ │
│ │ - POST /chat │ │
│ │ - POST /greeting │ │
│ │ - GET /profile/<phone> │ │
│ │ - GET /partner/<phone>/summary │ │
│ │ - POST /partner/<phone>/flag │ │
│ │ - GET /health │ │
│ │ - GET /offline │ │
│ └─────────────────────────────────────┘ │
│ │
│ ┌─────────────────────────────────────┐ │
│ │ Gemini Engine (LLM): │ │
│ │ - chat() │ │
│ │ - generate_greeting() │ │
│ │ - generate_session_summary() │ │
│ │ - generate_partner_summary() │ │
│ └─────────────────────────────────────┘ │
│ │
│ ┌─────────────────────────────────────┐ │
│ │ Groq STT: │ │
│ │ - transcribe_audio() │ │
│ └─────────────────────────────────────┘ │
│ │
│ ┌─────────────────────────────────────┐ │
│ │ Profile Manager (SQLite): │ │
│ │ - get_or_create_profile() │ │
│ │ - save_profile() │ │
│ │ - check_session_timeout() │ │
│ │ - add_message() │ │
│ │ - apply_profile_update() │ │
│ └─────────────────────────────────────┘ │
│ │
│ ┌─────────────────────────────────────┐ │
│ │ Knowledge Base (JSON, cached): │ │
│ │ - crops.json (54 entries) │ │
│ │ - health.json (17 scenarios) │ │
│ │ - schemes.json (15 programs) │ │
│ │ - referrals.json (5 districts) │ │
│ └─────────────────────────────────────┘ │
└─────────────────┬──────────────────────────┘
 │
 │ JSON response
 ↓
 ┌─────────────┐
 │ SQLite DB │
 │ samadhan.db │
 └─────────────┘
```

### Request-Response Lifecycle

**Example: Farmer asks about wheat rust**

```
1. FRONTEND (Browser)
 - User speaks: "गेहूं में जंग है"
 - Groq Whisper transcribes → "गेहूं में जंग है"
 - Input fields: text, phone, district (dehradun), audio_b64

2. BACKEND (Flask /chat endpoint)
 - Validate phone, audio size, input length
 - Call Groq STT (if audio_b64 provided)
 - Get/create farmer profile (phone = key)
 - Check session timeout (30 min limit)
 - Add message to chat history

3. GEMINI ENGINE
 - Build system prompt with:
 * 54 crops knowledge
 * 17 health scenarios
 * 15 schemes
 * Dehradun-specific referrals
 * Current season hint (April = रबी कटाई)
 * Chat history (last 10 messages)
 - Call gemini-2.5-flash model
 - Parse response: clean_text + <profile_update> JSON

4. RESPONSE EXTRACTION
 - Extract: domain (agriculture), entities (wheat, rust, mancozeb)
 - Update profile: add crop/problem/season to timeline
 - Select Dehradun referrals (KVK Roorkee, District Hospital)

5. DATABASE UPDATE
 - Save updated profile (flags, timeline, summary)
 - Save message pair (user + assistant)
 - Log domain classification

6. RETURN TO FRONTEND
 {
 "response": "गेहूं में गेरी (रतुआ) यानी जंग की बीमारी हो गई है। मैन्कोज़ेब 75 WP का 2.5 ग्राम प्रति लीटर पानी में घोल बनाकर छिड़काव करें। 10-15 दिन बाद फिर करें।",
 "domain": "agriculture",
 "profile_update": {
 "crop": "wheat",
 "problem": "rust",
 "entities_extracted": {...}
 }
 }

7. FRONTEND DISPLAYS
 - Response in a chat bubble
 - Domain icon ( for agriculture)
 - Timestamp
 - If failed: show "दोबारा कोशिश करें" button
```

---

## Why This Architecture

Every architecture decision in Samadhan was driven by a **problem we actually faced** during development:

| Decision | What We Chose | What We Rejected | Why |
|----------|--------------|-----------------|-----|
| **Agent Model** | Single Gemini call with 4-tier prompt | 3 separate agents (crop/health/scheme) + router | Previous router had 64-token truncation bug, double latency, and routing errors. Single call lets Gemini classify domain internally with full context |
| **Memory System** | 4-layer (active session → archive → profile → timeline) | Simple last-5-messages history | Farmers expect cross-session continuity ("वह spray काम नहीं किया, मैंने क्या ग़लत किया?"). Need session summaries + timeline for seasonal context, not just message history |
| **Knowledge Tier** | 3-tier (verified → general with disclaimer → redirect) | Binary know/don't-know | Saying "I don't know" kills trust. Tier 2 gives general guidance with safety disclaimers. Farmer always gets *something useful* even outside Tier 1 |
| **Storage** | SQLite with JSON profile_data | PostgreSQL / MongoDB | Embedded DB, zero setup, sufficient for V1 scale. JSON column gives schema flexibility during rapid iteration. No networking during rural downtime |
| **STT Engine** | Groq Whisper (server-side) | Browser Web Speech API | Browser STT is inconsistent for Hindi dialects. Groq handles Khariboli accent + field noise significantly better. Off-device = works offline if queued |
| **Frontend** | PWA (React) | Native iOS/Android app | Installable without app store hurdles. Works offline. No WhatsApp business verification needed for early adoption |
| **Session Timeout** | 30 minutes | None (persist forever) | Farmers get distracted (2-hour gaps between messages are common). 30 min = clean session boundary without losing context via archive + summary |
| **Rate Limiting** | 30/min on /chat | No limits | Free-tier Gemini has 1500 RPD ≈ 25/min sustained. Rate limiting prevents runaway abuse consuming all quota |

**Philosophy:** Don't build for the "typical user." Build for the farmer who has signal 2 hours a day, uses a 5-year-old phone, and might not read your error messages in English.

---

## Database Schema

### SQLite Tables

#### `farmers`
```sql
CREATE TABLE farmers (
 phone TEXT PRIMARY KEY, -- "+91XXXXXXXXXX" or "guest_TIMESTAMP"
 name TEXT DEFAULT '', -- "राजीव कुमार"
 village TEXT DEFAULT '',
 district TEXT DEFAULT '', -- "dehradun", "haridwar", etc.
 registered_at DATETIME,
 profile_data JSON, -- Farmer's full profile (see below)
 INDEX idx_phone (phone)
);
```

#### `profile_data` JSON Structure
```json
{
 "name": "राजीव कुमार",
 "phone": "+919876543210",
 "district": "dehradun",
 "village": "डोईवाला",
 "flags": ["follow_up_needed", "emergency"],
 "active_session": {
 "started_at": "2026-04-16T08:00:00",
 "message_count": 5,
 "messages": [
 {
 "role": "user",
 "text": "मेरी गेहूं में जंग है",
 "domain": "agriculture",
 "has_image": false,
 "timestamp": "2026-04-16T08:05:00"
 },
 {
 "role": "assistant",
 "text": "गेहूं में गेरी...",
 "domain": "agriculture",
 "timestamp": "2026-04-16T08:05:10"
 }
 ],
 "summary": null
 },
 "archived_sessions": [
 {
 "id": "guest_1776346400000_1",
 "started_at": "2026-04-15T15:30:00",
 "summary": "Farmer asked about onion purple blotch, received Mancozeb treatment advice."
 }
 ],
 "timeline": [
 {
 "date": "2026-04-16",
 "domain": "agriculture",
 "summary": "Asked about wheat rust, provided ICAR-verified Mancozeb treatment.",
 "status": "resolved"
 }
 ]
}
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Phone as Primary Key** | Farmer identification; supports guest mode (guest_TIMESTAMP) |
| **JSON Profile Data** | Flexible schema; supports flags, timeline, sessions without schema migration |
| **Session Timeout (30 min)** | Prevents old conversations mixing with new ones; mobile data conservation |
| **Message Archiving** | Keeps active_session lean; archived_sessions for history |
| **Timeline** | One-line domain + summary per interaction (for partner worker overview) |
| **Flags** | ASHA workers mark farmers for follow-up (emergency, deadline, etc.) |

---

## API Endpoints

### Public Endpoints (No Auth)

#### 1. **POST /chat**
Chat with Samadhan Mitra.

**Request:**
```json
{
 "text": "मेरी गेहूं में जंग है",
 "phone": "+919876543210",
 "district": "dehradun",
 "name": "राजीव कुमार",
 "audio_b64": "<base64 60-sec audio>",
 "image_b64": "<base64 crop photo>",
 "session_id": "guest_1776346400000"
}
```

**Response:**
```json
{
 "response": "गेहूं में गेरी (रतुआ) यानी जंग की बीमारी...",
 "domain": "agriculture",
 "transcription": "मेरी गेहूं में जंग है"
}
```

**Parameters Handled:**
- Phone validation (5+ digits or "unknown")
- Text truncation (max 1000 chars)
- Audio size limit (max 14 MB = 60 sec)
- Image size limit (max 9 MB)
- Timeout handling (model cascade)
- Rate limiting (30/min)

---

#### 2. **POST /greeting**
Get a personalized greeting.

**Request:**
```json
{
 "phone": "+919876543210"
}
```

**Response:**
```json
{
 "greeting": "नमस्ते राजीव जी! कैसा चल रहा है सब? पिछली बार गेहूं का सवाल पूछा था, उम्मीद है समस्या हल हो गई होगी।"
}
```

**Parameters Handled:**
- Context-aware (references last interaction)
- Flags consideration (if emergency set, mention urgency)
- Model fallback (if Gemini unavailable)

---

#### 3. **GET /health**
Backend health check.

**Response:**
```json
{
 "status": "ok",
 "service": "Samadhan Mitra"
}
```

**Parameters Handled:**
- Database connectivity check (implicit)
- Response time < 100ms

---

#### 4. **GET /offline**
Pre-cached Q&A for offline mode.

**Response:**
```json
{
 "cache": [
 {
 "id": 1,
 "query": "धान में कीड़े लग गए हैं",
 "response": "धान में तना छेदक लगा होगा। क्लोरपायरीफोस 20EC की 2 मिली/लीटर छिड़काव करें।"
 },
 ...
 ]
}
```

**Count:** 15 pre-cached responses

---

### Protected Endpoints (X-Partner-Token Required)

#### 5. **GET /profile/<phone>**
Get farmer profile (ASHA worker view).

**Headers:**
```
X-Partner-Token: <your_partner_token>
```

**Response:**
```json
{
 "name": "राजीव कुमार",
 "phone": "+919876543210",
 "district": "dehradun",
 "flags": ["follow_up_needed"],
 "active_session": {...},
 "timeline": [...]
}
```

**Parameters Handled:**
- Token validation (401 if missing/invalid)
- Phone formatting normalization

---

#### 6. **GET /partner/<phone>/summary**
AI-generated one-paragraph summary for home visit.

**Headers:**
```
X-Partner-Token: <your_partner_token>
```

**Response:**
```json
{
 "summary": "राजीव एक सीमांत किसान हैं जो देहरादून के डोईवाला गांव में 2 बीघा गेहूं उगाते हैं। पिछले सप्ताह गेहूं में जंग की बीमारी से संपर्क हुआ और मैंने मैन्कोज़ेब स्प्रे की सलाह दी। अभी अनुवर्ती जांच की जरूरत है। वे PM-किसान योजना के बारे में भी पूछ रहे हैं।"
}
```

**Parameters Handled:**
- Token validation
- Timeline aggregation (max 10 entries)
- Flags summary
- Session history consideration

---

#### 7. **POST /partner/<phone>/flag**
Add or remove flags on farmer profile.

**Headers:**
```
X-Partner-Token: <your_partner_token>
```

**Request:**
```json
{
 "flag": "follow_up_needed",
 "action": "add"
}
```

**Valid Flags:**
- `follow_up_needed` — Routine check-in required
- `emergency` — Urgent situation (pest outbreak, health issue)
- `upcoming_deadline` — Scheme application deadline approaching
- `unresolved_problem` — Issue not yet solved
- `resolved` — Problem resolved, no further action

**Response:**
```json
{
 "success": true,
 "flags": ["follow_up_needed", "emergency"]
}
```

**Parameters Handled:**
- Token validation (401 if missing)
- Flag value validation (400 if invalid flag)
- Action: "add" or "remove"
- Idempotent (adding duplicate flag = no change)
- Database persistence

---

## Knowledge Base

### 1. **crops.json** (54 entries)
Crop diseases, pests, problems with ICAR-verified treatments.

**Structure (per entry):**
```json
{
 "crop": "wheat",
 "problem": "rust (गेरी)",
 "local_names": ["रतुआ", "rust"],
 "symptoms": "नारंगी-भूरे दाने पत्तियों पर, सूखा दिखना, वायु से फैलता है",
 "cause": "Puccinia fungus, wet weather 15-25°C",
 "treatment": "Mancozeb 75 WP: 2.5 ग्राम/लीटर, 10-15 दिन अंतर",
 "prevention": "रोग-रोधी किस्में, खेत स्वच्छता, फसल चक्र",
 "escalation": "अगर 30% पत्तियां प्रभावित हों तो KVK से संपर्क करें",
 "source": "ICAR, PAU Advisory"
}
```

**Coverage:**
- Wheat (5 diseases)
- Rice (4 diseases)
- Cotton (3 pests)
- Onion (3 problems)
- Chili (2 problems)
- Potato (2 problems)
- Mango (2 problems)
- General (waterlogging, heat stress)
- ...Total: 54 entries

---

### 2. **health.json** (17 scenarios)
Occupational & seasonal health triage (not diagnosis).

**Structure (per scenario):**
```json
{
 "scenario": "pesticide_poisoning",
 "symptoms_described": ["उल्टी", "सिरदर्द", "कमजोरी", "बेचैनी"],
 "immediate_advice": "खेत छोड़ो, ताजी हवा में बैठो, कपड़े बदलो, त्वचा धो",
 "seek_help_when": "लक्षण 30 मिनट में ठीक न हों या बढ़ें",
 "where_to_go": "Primary Health Center (PHC) या District Hospital (जहर की दवा के लिए)",
 "ayushman_relevant": true,
 "emergency_signs": ["सांस लेने में कठिनाई", "बेहोशी", "झटके"],
 "NEVER_do": "किसी को उल्टी न कराएं, पानी न पिलाएं अगर निगलने में परेशानी हो"
}
```

**Scenarios:**
- Pesticide poisoning
- Fever (general, malaria, dengue)
- Cough (>2 weeks → TB screening)
- Hypertension signs
- Diabetes management
- Women's anemia
- Malnutrition (children)
- Heat stroke (Loo)

**Rule:** NEVER diagnose or prescribe specific medicines (except basic Paracetamol/ORS).

---

### 3. **schemes.json** (15 schemes)
Government programs with eligibility, documents, benefits.

**Structure (per scheme):**
```json
{
 "scheme": "PM_KISAN_MAANDHAN",
 "name": "पीएम-किसान मानधन",
 "full_name": "Pradhan Mantri Kisan Maandhan Yojana",
 "benefit": "₹3000 प्रति माह पेंशन 60 साल के बाद",
 "eligibility": "Age 18-40, छोटे/सीमांत किसान, PCOS रजिस्टर में",
 "documents_needed": ["आधार", "बैंक खाता", "खसरा-खतौनी"],
 "how_to_apply": "CSC या नजदीकी बैंक से संपर्क करें, ऑनलाइन pmkisan.gov.in",
 "helpline": "1800-180-1551 (सुबह 6 - रात 10)",
 "key_dates": "वर्षभर, कोई कट-ऑफ नहीं"
}
```

**Schemes:**
- PM-Kisan (₹6000/year)
- PM-Kisan Maandhan (₹3000/month pension)
- PM-KUSUM (Solar pumps, 60-90% subsidy)
- e-NAM (Online marketplace)
- Crop Insurance (PMFBY)
- Kisan Credit Card
- Seed Subsidy (50% discount)
- GOBAR-DHAN (Biogas)
- ... Total: 15 schemes

---

### 4. **referrals.json** (District-Structured)
Local contacts for agriculture, health, schemes.

**Structure:**
```json
{
 "generic": [
 {
 "name": "एम्बुलेंस (इमरजेंसी)",
 "type": "Emergency",
 "phone": "108",
 "hours": "24 घंटे"
 },
 {
 "name": "किसान कॉल सेंटर",
 "type": "Helpline",
 "phone": "1800-180-1551",
 "hours": "सुबह 6 - रात 10, सातों दिन"
 }
 ],
 "dehradun": [
 {
 "name": "कृषि विज्ञान केंद्र (KVK) देहरादून",
 "type": "KVK",
 "address": "देहरादून जिला",
 "phone": "0135-2720123",
 "hours": "सोमवार-शुक्रवार, 10 AM - 5 PM"
 },
 {
 "name": "दून हॉस्पिटल",
 "type": "Hospital",
 "address": "राजपुर रोड, देहरादून",
 "phone": "0135-2654321",
 "hours": "24 घंटे"
 }
 ],
 "haridwar": [...],
 "saharanpur": [...],
 "meerut": [...],
 "muzaffarnagar": [...]
}
```

**Coverage:** 5 districts × 6-8 contacts each + 7 generic helplines = 37+ referrals

---

## Configuration

### Environment Variables (.env)

```bash
# Google Gemini API — Get from https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Groq Whisper API (STT) — Get from https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here

# Flask Configuration
FLASK_ENV=development # or "production"
FLASK_PORT=5001
FLASK_DEBUG=False # Never True in production

# Partner Authentication (Change in production)
PARTNER_TOKEN=<your_secure_token>

# Database (local SQLite)
DATABASE_PATH=/app/samadhan.db # Docker: /app/samadhan.db
```

> **Never commit `.env` file to Git.** It's already in `.gitignore`. Use `.env.example` as a template instead.

### Rate Limiting Defaults
- `/chat`: 30 requests/minute
- `/greeting`: 20 requests/minute
- `/health`: Unlimited
- Global: 200/day per IP

### Session Defaults
- Timeout: 30 minutes
- Max messages/session: 20
- Audio max: 60 seconds (≈ 14 MB base64)
- Image max: 5 MB (9 MB base64)
- Text input max: 1000 characters

---

## Installation & Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for frontend)
- **SQLite 3** (included with Python)
- **Git**

### Backend Setup

```bash
# Navigate to backend directory
cd samadhan/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with API keys (never commit this!)
# Get keys from: https://aistudio.google.com (Gemini), https://console.groq.com (Groq)
cat > .env << 'EOF'
GEMINI_API_KEY=<your_api_key_here>
GROQ_API_KEY=<your_api_key_here>
FLASK_ENV=development
FLASK_PORT=5001
PARTNER_TOKEN=<your_secure_token>
EOF

# Important: .env is in .gitignore and should NOT be committed

# Verify setup
python3 -c "from agents.gemini_engine import chat; print(' Backend ready')"
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd samadhan/frontend

# Install dependencies
npm install

# Create .env (if needed)
echo "VITE_API_URL=http://localhost:5001" > .env

# Verify build
npm run build
echo " Frontend ready"
```

---

## Running the Application

### Option 1: Development (Separate Terminals)

**Terminal 1 — Backend:**
```bash
cd samadhan/backend
source venv/bin/activate
python3 app.py
# Output: "Running on http://localhost:5001"
```

**Terminal 2 — Frontend:**
```bash
cd samadhan/frontend
npm run dev
# Output: "VITE v5.4.21 ready in 153 ms, Local: http://localhost:5173"
```

**Access:** http://localhost:5173

---

### Option 2: Production with Nginx (Docker)

See [Docker Deployment](#docker-deployment) section below.

---

## Testing

### Backend Tests

**Health Check:**
```bash
curl http://localhost:5001/health
# {"status": "ok", "service": "Samadhan Mitra"}
```

**Chat Endpoint:**
```bash
curl -X POST http://localhost:5001/chat \
 -H "Content-Type: application/json" \
 -d '{
 "text": "मेरी गेहूं में जंग है",
 "phone": "+919876543210",
 "district": "dehradun"
 }'
# Returns: {"response": "...", "domain": "agriculture"}
```

**Partner Flag Endpoint:**
```bash
curl -X POST http://localhost:5001/partner/+919876543210/flag \
 -H "Content-Type: application/json" \
 -H "X-Partner-Token: <your_partner_token>" \
 -d '{"flag": "follow_up_needed", "action": "add"}'
# Returns: {"success": true, "flags": ["follow_up_needed"]}
```

**Unauthorized Access (Should Fail):**
```bash
curl -X POST http://localhost:5001/partner/+919876543210/flag \
 -H "Content-Type: application/json" \
 -d '{"flag": "emergency"}'
# Returns: 401 Unauthorized
```

### Frontend Tests

1. **Onboarding Flow:**
 - Clear `sessionStorage`
 - Reload page
 - Verify modal appears
 - Fill name + district → Submit
 - Verify `samadhan_district` saved in `sessionStorage`

2. **Chat Message:**
 - Type Hindi query
 - Send message
 - Verify response appears within 10 sec
 - Check domain classification (icon appears)

3. **Connection Status:**
 - Watch navbar status dot
 - Should be green (health check passed)
 - Network offline → dot turns red

4. **Retry Button:**
 - Force API error (disconnect network)
 - Send message → should fail
 - Verify retry button appears
 - Reconnect → retry should succeed

---

## Docker Deployment

> **Note for Judges:** Docker is for production deployment. For quick testing, use the "Development" mode in "Running the Application" section above. This section is optional.

### Building Images

```bash
# From project root
cd /path/to/Samadhan_TinkerQuest

# Build both images
docker build -t samadhan-backend:latest samadhan/backend/
docker build -t samadhan-frontend:latest samadhan/frontend/
```

### Running with Docker Compose

```bash
# From project root
docker-compose up -d

# Output:
# Creating samadhan_backend ...
# Creating samadhan_frontend ...
# WARNING: Image for service backend was built... but not found locally...

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Access application
# Frontend: http://localhost (port 80)
# Backend: http://localhost:5001 (direct access for testing)
```

### Health Checks

```bash
# Backend health
curl http://localhost:5001/health
# {"status": "ok", "service": "Samadhan Mitra"}

# Frontend (Nginx)
curl -I http://localhost/
# HTTP/1.1 200 OK

# Check container status
docker-compose ps
# STATUS: "Up X seconds (healthy)" for backend
```

### Environment Configuration in Docker

Create `.env` file in project root:

```env
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
FLASK_ENV=production
PARTNER_TOKEN=your_secret_token
```

Docker Compose will pass these to the backend container via `env_file: ./samadhan/backend/.env`

### Stopping & Cleanup

```bash
# Stop containers
docker-compose down

# Remove volumes (deletes database)
docker-compose down -v

# Remove all images
docker rmi samadhan-backend samadhan-frontend
```

### Production Deployment Checklist

- [ ] Update `GEMINI_API_KEY` with production key
- [ ] Update `GROQ_API_KEY` with production key
- [ ] Change `PARTNER_TOKEN` to strong secret
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Enable HTTPS (SSL certificates in Nginx)
- [ ] Whitelist frontend domain in CORS
- [ ] Set up database backups (weekly)
- [ ] Configure logging to persistent volume
- [ ] Monitor rate limits and quota usage

---

## Security Considerations

### 1. **API Key Protection**
- `.env` file in `.gitignore` (never commit secrets)
- Use environment variables, not hardcoded keys
- Rotate API keys quarterly
- Use separate keys for dev/prod

### 2. **Authentication**
- Partner endpoints use `X-Partner-Token` header
- Token validation on every protected endpoint
- No user passwords (stateless, phone-based)
- Session IDs are random (guest_TIMESTAMP format)

### 3. **Input Validation**
- Phone number validation (5+ digits or "unknown")
- Text truncation (max 1000 chars)
- Audio size limit (60 sec max ≈ 14 MB)
- Image size limit (5 MB max)
- JSON parsing with error handling

### 4. **Rate Limiting**
- 30 requests/min on `/chat` (prevents abuse)
- 20 requests/min on `/greeting`
- 200 requests/day per IP (global)
- Memory-based (no external dependency)

### 5. **Data Privacy**
- Farmer data stored locally (SQLite)
- No data sent to third-party services except Gemini/Groq (API calls only)
- Chat history purged after 30 min of inactivity
- Session timeout enforced
- Profile data protected behind partner token

### 6. **CORS Policy**
- Limited to `localhost:5173` in development
- Must be updated for production domain
- No wildcards (*) allowed

### 7. **SQL Injection Prevention**
- Using SQLAlchemy ORM (parameterized queries)
- Phone used as primary key (validated before use)
- No string concatenation in SQL

### 8. **Error Handling**
- Generic error messages to users (no stack traces)
- Detailed logs server-side (ISO timestamps)
- No sensitive data in error responses

---

## Performance Optimizations

### 1. **Knowledge Caching**
- Load JSON files once at startup, cache in memory
- Not reloaded per API call → ~50ms faster response
- Cache size: ~2 MB (crops + health + schemes + referrals)

### 2. **Model Cascade**
- Primary model: `gemini-2.5-flash` (1500 RPD free)
- Fallback model: `gemini-2.5-flash-lite` (if quota hit)
- Smart retry logic: 429 (quota) → skip retry, go to fallback
- Exponential backoff for 503 (server error)

### 3. **Session Management**
- 30-minute timeout (aggressive) → fewer stored sessions
- Max 20 messages per session → constrain history size
- Archive sessions after timeout → keep active_session lean
- Lazy load timeline (on-demand for partner view)

### 4. **Audio Processing**
- Groq Whisper (not browser-based) → faster STT
- Max 60 sec input (14 MB base64) → upload time < 5s on 4G
- OGG/WAV support → smaller file sizes

### 5. **Frontend Optimization**
- Vite (fast dev server with HMR)
- Inline CSS (no external stylesheet fetch)
- sessionStorage (fast, no network)
- Image lazy loading (if implemented)

### 6. **Database**
- SQLite (embedded, no network roundtrip)
- Index on phone column (fast lookups)
- JSON profile_data (no joins needed)
- Weekly backups (async, no blocking)

### 7. **API Response Time**
- Target: < 10 seconds (user expectation)
- Breakdown:
 - Network: 1-2 sec
 - Groq STT: 2-3 sec
 - Gemini API: 2-3 sec
 - Processing: 1-2 sec
 - Buffer: 1-2 sec

---

## Future Roadmap

### Phase 5: WhatsApp Integration
- [ ] Twilio WhatsApp Business API
- [ ] Farmer messages via WhatsApp → same `gemini_engine.chat()` call
- [ ] Voice note support (OGG → Groq transcription)
- [ ] Reach 100M+ farmers on WhatsApp

### Phase 6: IVR / Toll-Free
- [ ] Exotel platform integration (India-specific)
- [ ] Toll-free number (1800-XXX-XXXX)
- [ ] Farmer dials → records voice question (30 sec)
- [ ] Audio → Groq Whisper → Gemini → Google Cloud TTS
- [ ] Hindi voice playback to farmer
- [ ] Support farmers without smartphones

### Phase 7: CI/CD & Automation
- [ ] GitHub Actions: pytest on push, npm build validation
- [ ] Automated weekly DB backups to S3
- [ ] Slack notifications on errors
- [ ] Performance monitoring (response time, quota usage)

### Phase 8: Analytics & Insights
- [ ] Track query domains (agriculture vs health vs schemes)
- [ ] Measure resolution rates (did farmer's problem get solved?)
- [ ] Seasonal trends (peak query times)
- [ ] District-wise engagement
- [ ] Farmer cohort analysis

### Phase 9: Multi-Language Support
- [ ] Punjabi (for Punjab farmers)
- [ ] Marathi (for Maharashtra)
- [ ] Gujarati (for Gujarat)
- [ ] Bengali (for West Bengal)
- [ ] Model fine-tuning for regional languages

### Phase 10: Advanced Features
- [ ] Weather API integration (rainfall, temperature)
- [ ] Soil health assessment (NPK testing results)
- [ ] Market price tracking (mandi.gov.in API)
- [ ] Farmer-to-farmer peer network
- [ ] Expert on-demand (video call with KVK officer)

---

## Contributing

This project is open-source and welcomes contributions. See `/docs/CONTRIBUTING.md` for detailed guidelines, or submit a pull request directly.

**Code Style:** Python (PEP 8), JavaScript (ES2020+), JSON (2-space indent).

---

## License & Credits

**License:** MIT — See [LICENSE](LICENSE) file.

**Key Technologies:**
- ICAR (knowledge base sourcing)
- Google Gemini (LLM)
- Groq Whisper (STT)
- Flask & React (frameworks)

**Inspiration:** Farmers of UP & Uttarakhand

---

**Last Updated:** April 16, 2026 | **Version:** 1.0.0 | **Status:** Production Ready
