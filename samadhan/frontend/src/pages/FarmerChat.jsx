import React, { useState, useRef, useEffect, useCallback } from "react";
import MessageBubble from "../components/MessageBubble.jsx";
import VoiceInput from "../components/VoiceInput.jsx";

const API_BASE = "/api";

function nowTime() {
  return new Date().toLocaleTimeString("hi-IN", { hour: "2-digit", minute: "2-digit" });
}
function makeId() { return Math.random().toString(36).slice(2); }
// Auto-generate anonymous session ID — no login needed
function getSessionPhone() {
  let id = sessionStorage.getItem("samadhan_phone");
  if (!id) { id = "guest_" + Date.now(); sessionStorage.setItem("samadhan_phone", id); }
  return id;
}

const FALLBACK = [
  { query: "धान कीड़े", response: "तना छेदक लगा होगा। क्लोरपायरीफोस 20EC (2 मिली/लीटर) सुबह-शाम छिड़काव करें।" },
  { query: "गेहूं पीली", response: "Rust fungus या नाइट्रोजन की कमी। Mancozeb 2.5 ग्राम/लीटर स्प्रे करें।" },
  { query: "PM किसान", response: "PM किसान में ₹6000/साल मिलते हैं। pmkisan.gov.in पर रजिस्ट्रेशन करें।" },
  { query: "फसल बीमा", response: "PMFBY — बैंक या CSC केंद्र जाएं। बुवाई के 10 दिन के अंदर करें।" },
  { query: "बुखार", response: "पानी ज्यादा पिएं, आराम करें। 2 दिन से ज्यादा हो तो PHC जाएं।" },
  { query: "मिट्टी जांच", response: "नजदीकी KVK या कृषि विभाग में जाएं। मृदा स्वास्थ्य कार्ड मुफ्त मिलता है।" },
  { query: "खाद यूरिया", response: "यूरिया की कमी से पत्तियां पीली होती हैं। 20-25 किग्रा/बीघा डालें।" },
  { query: "सिंचाई पानी", response: "धान में 5-7 दिन में एक बार सिंचाई करें। गेहूं में 6 बार सिंचाई पर्याप्त है।" },
  { query: "टमाटर रोग", response: "टमाटर में झुलसा रोग हो सकता है। Mancozeb 2 ग्राम/लीटर का छिड़काव करें।" },
  { query: "सरसों कीड़े", response: "सरसों में माहू (Aphid) लग सकता है। Imidacloprid 0.3 मिली/लीटर स्प्रे करें।" },
  { query: "कपास", response: "कपास में बॉलवर्म के लिए Bt कपास लगाएं या Cypermethrin स्प्रे करें।" },
  { query: "आलू", response: "आलू में अगेती झुलसा के लिए Mancozeb + Metalaxyl स्प्रे 10 दिन के अंतर पर करें।" },
  { query: "किसान क्रेडिट", response: "किसान क्रेडिट कार्ड (KCC) के लिए नजदीकी बैंक जाएं। 3 लाख तक 4% ब्याज पर लोन मिलता है।" },
  { query: "मंडी भाव", response: "agmarknet.gov.in पर आज के मंडी भाव देखें या अपने जिले की कृषि मंडी से संपर्क करें।" },
  { query: "सोलर पंप", response: "PM-KUSUM योजना में 90% सब्सिडी पर सोलर पंप मिलता है। कृषि विभाग से आवेदन करें।" },
];

function offlineFallback(text, cache) {
  const t = text.toLowerCase();
  for (const f of cache) {
    const kw = (f.query || "").split(" ");
    if (kw.some((w) => w && t.includes(w))) return f.response;
  }
  return "इंटरनेट नहीं है। कृपया बाद में फिर कोशिश करें।";
}

const DISTRICTS = [
  "हरिद्वार", "देहरादून", "सहारनपुर", "मेरठ", "मुजफ्फरनगर",
  "बिजनौर", "अमरोहा", "बागपत", "गाजियाबाद", "शामली", "अन्य"
];
const DISTRICT_MAP = {
  "हरिद्वार": "haridwar", "देहरादून": "dehradun", "सहारनपुर": "saharanpur",
  "मेरठ": "meerut", "मुजफ्फरनगर": "muzaffarnagar",
};

function getOrSetDistrict() {
  return sessionStorage.getItem("samadhan_district") || null;
}

export default function FarmerChat() {
  const phone = getSessionPhone();
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [offlineCache, setOfflineCache] = useState(FALLBACK);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [district, setDistrict] = useState(getOrSetDistrict);
  const [showOnboarding, setShowOnboarding] = useState(!getOrSetDistrict());
  const [onboardName, setOnboardName] = useState("");
  const [onboardDistrict, setOnboardDistrict] = useState("");
  const [lastUserMsg, setLastUserMsg] = useState(null); // for retry
  const bottomRef = useRef(null);
  const fileInputRef = useRef(null);
  const sendLockRef = useRef(false);

  // Fetch offline cache
  useEffect(() => {
    fetch(`${API_BASE}/offline`)
      .then((r) => r.json())
      .then((d) => { if (d.cache?.length) setOfflineCache(d.cache); })
      .catch(() => {});
  }, []);

  // Fetch greeting once
  useEffect(() => {
    const fetchGreeting = async () => {
      try {
        const res = await fetch(`${API_BASE}/greeting`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ phone }),
        });
        if (res.ok) {
          const data = await res.json();
          if (data.greeting) {
            const msg = { id: makeId(), role: "assistant", text: data.greeting, domain: "general", timestamp: nowTime() };
            setMessages([msg]);
            speakText(data.greeting);
          }
        }
      } catch {
        setMessages([{ id: makeId(), role: "assistant", text: "नमस्ते! समाधान मित्र में आपका स्वागत है। आज मैं आपकी क्या मदद कर सकता हूँ?", domain: "general", timestamp: nowTime() }]);
      }
    };
    fetchGreeting();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const speakText = useCallback((text) => {
    if (!ttsEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = "hi-IN";
    utter.rate = 0.9;
    window.speechSynthesis.speak(utter);
  }, [ttsEnabled]);

  const handleOnboardingSubmit = () => {
    const d = DISTRICT_MAP[onboardDistrict] || onboardDistrict.toLowerCase();
    sessionStorage.setItem("samadhan_district", d);
    if (onboardName) sessionStorage.setItem("samadhan_name", onboardName);
    setDistrict(d);
    setShowOnboarding(false);
  };

  const sendMessage = useCallback(async ({ text, audio_b64, image_b64, imageDataUrl }) => {
    if ((!text && !audio_b64) || sendLockRef.current) return;
    sendLockRef.current = true;

    if (text) setLastUserMsg({ text, image_b64, imageDataUrl });

    const userMsg = { id: makeId(), role: "user", text: text || "🎙 आवाज़ संदेश", timestamp: nowTime(), image: imageDataUrl || null };
    setMessages((prev) => [...prev, userMsg]);
    setInputText("");
    setImageFile(null);
    setLoading(true);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);

    try {
      const body = { phone };
      if (text) body.text = text;
      if (audio_b64) body.audio_b64 = audio_b64;
      if (image_b64) body.image_b64 = image_b64;
      const d = district || sessionStorage.getItem("samadhan_district") || "";
      if (d) body.district = d;

      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      let data;
      try { data = await res.json(); } catch { throw new Error("Invalid response"); }

      if (audio_b64 && data.transcription) {
        setMessages((prev) => prev.map((m) => m.id === userMsg.id ? { ...m, text: data.transcription } : m));
      }

      const botMsg = { id: makeId(), role: "assistant", text: data.response, domain: data.domain, timestamp: nowTime() };
      setMessages((prev) => [...prev, botMsg]);
      speakText(data.response);

    } catch (err) {
      const isTimeout = err.name === "AbortError";
      const fallbackText = isTimeout
        ? "अनुरोध समय सीमा पार — कृपया दोबारा कोशिश करें।"
        : offlineFallback(text || "", offlineCache);
      setMessages((prev) => [...prev, {
        id: makeId(), role: "assistant",
        text: isTimeout ? fallbackText : `⚡ ऑफलाइन: ${fallbackText}`,
        domain: "general", timestamp: nowTime(), isFailed: true,
      }]);
    } finally {
      clearTimeout(timeout);
      setLoading(false);
      sendLockRef.current = false;
    }
  }, [phone, district, offlineCache, speakText]);

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() && !imageFile) return;
    sendMessage({ text: inputText.trim() || (imageFile ? "इस फसल में क्या समस्या है?" : ""), image_b64: imageFile?.base64, imageDataUrl: imageFile?.dataUrl });
  };

  const handleAudioReady = useCallback((b64) => sendMessage({ audio_b64: b64 }), [sendMessage]);
  const handleTranscript = useCallback((text) => { if (text) sendMessage({ text }); }, [sendMessage]);

  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { alert("फोटो 5MB से छोटी होनी चाहिए।"); return; }
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target.result;
      setImageFile({ dataUrl, base64: dataUrl.split(",")[1] });
    };
    reader.readAsDataURL(file);
    e.target.value = "";
  };

  return (
    <div style={chatContainerStyle}>
      {/* District Onboarding Modal */}
      {showOnboarding && (
        <div style={modalOverlayStyle}>
          <div style={modalBoxStyle}>
            <div style={{ fontSize: "1.8rem", marginBottom: 8 }}>🌾</div>
            <div style={{ fontWeight: 800, fontSize: "1.1rem", color: "#1a6b3c", marginBottom: 4 }}>नमस्ते! पहले थोड़ी जानकारी</div>
            <div style={{ fontSize: "0.82rem", color: "#555", marginBottom: 16 }}>बेहतर मदद के लिए — छोड़ भी सकते हैं</div>
            <input
              placeholder="आपका नाम (वैकल्पिक)"
              value={onboardName} onChange={(e) => setOnboardName(e.target.value)}
              style={modalInputStyle}
            />
            <select value={onboardDistrict} onChange={(e) => setOnboardDistrict(e.target.value)} style={modalInputStyle}>
              <option value="">जिला चुनें (वैकल्पिक)</option>
              {DISTRICTS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
            <button onClick={handleOnboardingSubmit} style={modalBtnStyle}>शुरू करें ➤</button>
            <button onClick={() => setShowOnboarding(false)} style={{ background: "none", border: "none", color: "#888", cursor: "pointer", fontSize: "0.8rem", marginTop: 6 }}>छोड़ें</button>
          </div>
        </div>
      )}

      {/* Header */}
      <div style={chatHeaderStyle}>
        <div style={avatarStyle}>🤖</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>समाधान मित्र</div>
          <div style={{ fontSize: "0.72rem", opacity: 0.85 }}>हिंदी में बात करें · कृषि · स्वास्थ्य · योजना</div>
        </div>
        <button
          onClick={() => { setTtsEnabled((v) => !v); window.speechSynthesis?.cancel(); }}
          title={ttsEnabled ? "आवाज़ बंद करें" : "आवाज़ चालू करें"}
          style={{ background: "rgba(255,255,255,0.15)", border: "none", borderRadius: 20, padding: "4px 10px", color: "#fff", cursor: "pointer", fontSize: "1rem" }}
        >
          {ttsEnabled ? "🔊" : "🔇"}
        </button>
        <div style={{ display: "flex", gap: 4, marginLeft: 8 }}>
          <span style={dotStyle("#4caf50")} /><span style={dotStyle("#2196f3")} /><span style={dotStyle("#ff9800")} />
        </div>
      </div>

      {/* Messages */}
      <div style={messagesAreaStyle}>
        {messages.length === 0 && !loading && (
          <div style={emptyStyle}>
            <div style={{ fontSize: "2.5rem", marginBottom: 8 }}>🎙</div>
            <div style={{ fontWeight: 700, color: "#1a6b3c", marginBottom: 6 }}>नमस्ते किसान भाई/बहन!</div>
            <div style={{ fontSize: "0.88rem", color: "#666", lineHeight: 1.7 }}>
              नीचे बड़े बटन को दबाकर बोलें<br />या टाइप करके सवाल पूछें।<br />📷 फसल की फोटो भी भेज सकते हैं।
            </div>
          </div>
        )}
        {messages.map((msg) => (
          <React.Fragment key={msg.id}>
            <MessageBubble message={msg} />
            {msg.isFailed && lastUserMsg && (
              <div style={{ textAlign: "center", marginBottom: 8 }}>
                <button
                  onClick={() => { setMessages((prev) => prev.filter((m) => m.id !== msg.id)); sendMessage(lastUserMsg); }}
                  style={{ background: "#fff", border: "1.5px solid #1a6b3c", color: "#1a6b3c", borderRadius: 16, padding: "4px 16px", fontSize: "0.8rem", cursor: "pointer" }}
                >
                  🔄 दोबारा कोशिश करें
                </button>
              </div>
            )}
          </React.Fragment>
        ))}
        {loading && (
          <div style={{ display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 10 }}>
            <div style={loadingBubbleStyle}>
              <span style={{ fontSize: "0.85rem", color: "#1a6b3c" }}>समाधान सोच रहा है</span>
              {[0, 0.33, 0.66].map((d, i) => <span key={i} style={dotAnim(d)}>●</span>)}
              <style>{`@keyframes blink { 50% { opacity: 0 } }`}</style>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Image preview */}
      {imageFile && (
        <div style={imgPreviewStyle}>
          <img src={imageFile.dataUrl} alt="preview" style={{ height: 52, borderRadius: 8, objectFit: "cover", border: "2px solid #c8e6c9" }} />
          <span style={{ fontSize: "0.8rem", color: "#555", flex: 1 }}>📷 फोटो तैयार — संदेश भेजें</span>
          <button onClick={() => setImageFile(null)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1rem", color: "#d32f2f" }}>✕</button>
        </div>
      )}

      {/* Input area — voice first */}
      <div style={inputAreaStyle}>
        {/* Big voice button */}
        <div style={{ display: "flex", justifyContent: "center", paddingBottom: 8 }}>
          <VoiceInput onAudioReady={handleAudioReady} onTranscript={handleTranscript} disabled={loading} large />
        </div>

        {/* Text input row */}
        <form onSubmit={handleTextSubmit} style={inputRowStyle}>
          <button type="button" title="फोटो भेजें" onClick={() => fileInputRef.current?.click()} disabled={loading} style={iconBtn(loading)}>📷</button>
          <input ref={fileInputRef} type="file" accept="image/*" capture="environment" style={{ display: "none" }} onChange={handleImageChange} />
          <input
            type="text" placeholder="यहाँ टाइप करें…" value={inputText}
            onChange={(e) => setInputText(e.target.value)} disabled={loading} style={textInputStyle}
          />
          {(inputText.trim() || imageFile) && (
            <button type="submit" disabled={loading} style={sendBtnStyle(loading)}>➤</button>
          )}
        </form>
      </div>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const chatContainerStyle = { flex: 1, display: "flex", flexDirection: "column", maxWidth: 680, width: "100%", margin: "0 auto", background: "#e8f5e980" };
const chatHeaderStyle = { background: "linear-gradient(135deg, rgba(26,107,60,0.9), rgba(46,125,50,0.9))", backdropFilter: "blur(10px)", color: "#fff", padding: "12px 18px", display: "flex", alignItems: "center", gap: 12, boxShadow: "0 4px 12px rgba(0,0,0,0.1)", position: "sticky", top: 0, zIndex: 10 };
const avatarStyle = { width: 40, height: 40, borderRadius: "50%", background: "rgba(255,255,255,0.2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.2rem" };
const dotStyle = (c) => ({ width: 8, height: 8, borderRadius: "50%", background: c, display: "inline-block", boxShadow: `0 0 4px ${c}` });
const messagesAreaStyle = { flex: 1, overflowY: "auto", padding: "16px 14px", display: "flex", flexDirection: "column", background: "linear-gradient(180deg, #f0f9f0 0%, #e8f5e9 100%)" };
const emptyStyle = { textAlign: "center", marginTop: 40, padding: "0 20px" };
const loadingBubbleStyle = { background: "#fff", borderRadius: "18px 18px 18px 4px", padding: "10px 16px", boxShadow: "0 1px 4px rgba(0,0,0,0.1)", display: "flex", alignItems: "center", gap: 4 };
const dotAnim = (d) => ({ animation: `blink 1s step-start ${d}s infinite`, fontSize: "0.7rem", color: "#1a6b3c" });
const imgPreviewStyle = { background: "#fff", borderTop: "1px solid #c8e6c9", padding: "10px 14px", display: "flex", alignItems: "center", gap: 12 };
const inputAreaStyle = { background: "rgba(255,255,255,0.9)", backdropFilter: "blur(8px)", borderTop: "1px solid rgba(200,230,201,0.5)", padding: "12px 14px 16px", boxShadow: "0 -4px 12px rgba(0,0,0,0.03)", position: "sticky", bottom: 0 };
const inputRowStyle = { display: "flex", gap: 8, alignItems: "center" };
const iconBtn = (l) => ({ flexShrink: 0, background: "none", border: "none", cursor: l ? "not-allowed" : "pointer", fontSize: "1.3rem", padding: "4px", opacity: l ? 0.4 : 1 });
const textInputStyle = { flex: 1, border: "1.5px solid #e0e0e0", borderRadius: 22, padding: "10px 18px", fontSize: "0.95rem", outline: "none", background: "#fafafa" };
const sendBtnStyle = (l) => ({ flexShrink: 0, width: 44, height: 44, borderRadius: "50%", border: "none", background: l ? "#e0e0e0" : "linear-gradient(135deg, #1a6b3c, #2e7d32)", color: "#fff", fontSize: "1.1rem", cursor: l ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 4px 10px rgba(26,107,60,0.2)" });
const modalOverlayStyle = { position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 };
const modalBoxStyle = { background: "#fff", borderRadius: 20, padding: "28px 24px", maxWidth: 320, width: "90%", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", boxShadow: "0 20px 60px rgba(0,0,0,0.2)" };
const modalInputStyle = { width: "100%", border: "1.5px solid #e0e0e0", borderRadius: 12, padding: "10px 14px", fontSize: "0.95rem", marginBottom: 10, boxSizing: "border-box", outline: "none" };
const modalBtnStyle = { width: "100%", background: "linear-gradient(135deg, #1a6b3c, #2e7d32)", color: "#fff", border: "none", borderRadius: 12, padding: "12px", fontSize: "1rem", cursor: "pointer", fontWeight: 700, marginTop: 4 };
