import React, { useState, useRef, useEffect, useCallback } from "react";
import MessageBubble from "../components/MessageBubble.jsx";
import VoiceInput from "../components/VoiceInput.jsx";

const API_BASE = "/api";

function nowTime() {
  return new Date().toLocaleTimeString("hi-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function makeId() {
  return Math.random().toString(36).slice(2);
}

// Offline fallback
const FALLBACK = [
  { query: "धान में कीड़े", response: "तना छेदक लगा होगा। क्लोरपायरीफोस 20EC (2 मिली/लीटर) का छिड़काव करें।" },
  { query: "गेहूं पीली", response: "Rust fungus या नाइट्रोजन की कमी। Mancozeb 2.5 ग्राम/लीटर स्प्रे करें।" },
  { query: "PM किसान", response: "PM किसान में ₹6000/साल मिलते हैं। pmkisan.gov.in पर रजिस्ट्रेशन करें।" },
  { query: "फसल बीमा", response: "PMFBY — बैंक या CSC केंद्र जाएं। बुवाई के 10 दिन के अंदर करें।" },
  { query: "बुखार", response: "पानी ज्यादा पिएं, आराम करें। 2 दिन से ज्यादा हो तो PHC जाएं।" },
];

function offlineFallback(text, cache) {
  const t = text.toLowerCase();
  for (const f of cache) {
    const keywords = (f.query || "").split(" ");
    if (keywords.some((w) => w && t.includes(w))) return f.response;
  }
  return "इंटरनेट नहीं है। कृपया बाद में फिर कोशिश करें।";
}

export default function FarmerChat() {
  const [phone, setPhone] = useState("");
  const [phoneSubmitted, setPhoneSubmitted] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [offlineCache, setOfflineCache] = useState(FALLBACK);
  const [greetingLoaded, setGreetingLoaded] = useState(false);
  const bottomRef = useRef(null);
  const fileInputRef = useRef(null);

  // Fetch offline cache
  useEffect(() => {
    fetch(`${API_BASE}/offline`)
      .then((r) => r.json())
      .then((data) => { if (data.cache?.length) setOfflineCache(data.cache); })
      .catch(() => { });
  }, []);

  // Auto-scroll on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Fetch proactive greeting when phone is submitted
  useEffect(() => {
    if (!phoneSubmitted || greetingLoaded) return;

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
            setMessages([{
              id: makeId(),
              role: "assistant",
              text: data.greeting,
              domain: "general",
              timestamp: nowTime(),
            }]);

            // Speak the greeting
            if (window.speechSynthesis) {
              const utter = new SpeechSynthesisUtterance(data.greeting);
              utter.lang = "hi-IN";
              utter.rate = 0.9;
              window.speechSynthesis.speak(utter);
            }
          }
        }
      } catch (err) {
        // Fallback greeting
        setMessages([{
          id: makeId(),
          role: "assistant",
          text: "नमस्ते! समाधान मित्र में आपका स्वागत है। आज मैं आपकी क्या मदद कर सकता हूँ?",
          domain: "general",
          timestamp: nowTime(),
        }]);
      }
      setGreetingLoaded(true);
    };

    fetchGreeting();
  }, [phoneSubmitted, phone, greetingLoaded]);

  // Send message (text or with image)
  const sendMessage = useCallback(
    async ({ text, audio_b64, image_b64, imageDataUrl }) => {
      if (!text && !audio_b64) return;

      const userMsg = {
        id: makeId(),
        role: "user",
        text: text || "🎙 आवाज़ संदेश",
        timestamp: nowTime(),
        image: imageDataUrl || null,
      };
      setMessages((prev) => [...prev, userMsg]);
      setInputText("");
      setImageFile(null);
      setLoading(true);

      try {
        const body = {
          phone: phone || "unknown",
        };
        if (text) body.text = text;
        if (audio_b64) body.audio_b64 = audio_b64;
        if (image_b64) body.image_b64 = image_b64;

        const res = await fetch(`${API_BASE}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        // If audio was sent, update the user message with transcription
        if (audio_b64 && data.transcription) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === userMsg.id
                ? { ...m, text: data.transcription }
                : m
            )
          );
        }

        const botMsg = {
          id: makeId(),
          role: "assistant",
          text: data.response,
          domain: data.domain,
          timestamp: nowTime(),
        };

        // Speak the response
        if (data.response && window.speechSynthesis) {
          const utter = new SpeechSynthesisUtterance(data.response);
          utter.lang = "hi-IN";
          utter.rate = 0.9;
          window.speechSynthesis.speak(utter);
        }

        setMessages((prev) => [...prev, botMsg]);
      } catch (err) {
        const fallbackText = offlineFallback(text || "", offlineCache);
        setMessages((prev) => [
          ...prev,
          {
            id: makeId(),
            role: "assistant",
            text: `⚡ ऑफलाइन: ${fallbackText}`,
            domain: "general",
            timestamp: nowTime(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [phone, offlineCache]
  );

  // Handlers
  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() && !imageFile) return;
    sendMessage({
      text: inputText.trim() || (imageFile ? "इस फसल में क्या समस्या है?" : ""),
      image_b64: imageFile?.base64,
      imageDataUrl: imageFile?.dataUrl,
    });
  };

  const handleAudioReady = (audioBase64) => {
    sendMessage({ audio_b64: audioBase64 });
  };

  const handleTranscript = (text) => {
    if (text) sendMessage({ text });
  };

  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      alert("फोटो 5MB से छोटी होनी चाहिए।");
      return;
    }
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target.result;
      const base64 = dataUrl.split(",")[1];
      setImageFile({ dataUrl, base64 });
    };
    reader.readAsDataURL(file);
    e.target.value = "";
  };

  // Phone gate
  if (!phoneSubmitted) {
    return (
      <div style={welcomeContainerStyle}>
        <div style={{ fontSize: "3.5rem", marginBottom: 4 }}>🌾</div>
        <h2 style={{ color: "#1a6b3c", fontWeight: 800, fontSize: "1.5rem", marginBottom: 4 }}>
          समाधान मित्र
        </h2>
        <p style={{ color: "#666", textAlign: "center", maxWidth: 340, lineHeight: 1.6, marginBottom: 8 }}>
          किसानों का अपना AI सहायक — फसल, स्वास्थ्य, सरकारी योजना, सब कुछ एक जगह
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (phone.replace(/\D/g, "").length >= 10) setPhoneSubmitted(true);
          }}
          style={{ display: "flex", flexDirection: "column", gap: 12, width: "100%", maxWidth: 340 }}
        >
          <input
            type="tel"
            placeholder="📱 मोबाइल नंबर डालें"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
            style={phoneInputStyle}
          />
          <button type="submit" style={startBtnStyle}>
            शुरू करें →
          </button>
        </form>
        <p style={{ color: "#aaa", fontSize: "0.72rem", marginTop: 16 }}>
          TinkerQuest 26 · IIT Roorkee · PS1 Samadhan
        </p>
      </div>
    );
  }

  // Main Chat UI
  return (
    <div style={chatContainerStyle}>
      {/* Chat header */}
      <div style={chatHeaderStyle}>
        <div style={avatarStyle}>🤖</div>
        <div>
          <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>समाधान मित्र</div>
          <div style={{ fontSize: "0.72rem", opacity: 0.85 }}>
            📱 {phone} · हिंदी में बात करें
          </div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 4 }}>
          <span style={domainDotStyle("#4caf50")} title="कृषि" />
          <span style={domainDotStyle("#2196f3")} title="स्वास्थ्य" />
          <span style={domainDotStyle("#ff9800")} title="योजना" />
        </div>
      </div>

      {/* Messages area */}
      <div style={messagesAreaStyle}>
        {messages.length === 0 && !loading && (
          <div style={emptyStateStyle}>
            <div style={{ fontSize: "2rem", marginBottom: 8 }}>👋</div>
            <div style={{ fontWeight: 600, marginBottom: 6, color: "#1a6b3c" }}>
              नमस्ते किसान भाई/बहन!
            </div>
            <div style={{ fontSize: "0.88rem", lineHeight: 1.6, color: "#666" }}>
              फसल की समस्या बताएं, सरकारी योजना पूछें, स्वास्थ्य सवाल करें।
              <br />
              🎙 बोलकर या ⌨️ टाइप करके पूछें। 📷 फोटो भी भेज सकते हैं।
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {loading && (
          <div style={{ display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 10 }}>
            <div style={loadingBubbleStyle}>
              <span style={{ fontSize: "0.85rem", color: "#1a6b3c" }}>
                समाधान सोच रहा है
              </span>
              <span style={dotAnimStyle(0)}>●</span>
              <span style={dotAnimStyle(0.33)}>●</span>
              <span style={dotAnimStyle(0.66)}>●</span>
              <style>{`@keyframes blink { 50% { opacity: 0 } }`}</style>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Image preview */}
      {imageFile && (
        <div style={imagePreviewStyle}>
          <img
            src={imageFile.dataUrl}
            alt="preview"
            style={{ height: 56, borderRadius: 10, objectFit: "cover", border: "2px solid #c8e6c9" }}
          />
          <span style={{ fontSize: "0.8rem", color: "#555", flex: 1 }}>
            📷 फोटो तैयार — संदेश भेजें
          </span>
          <button
            onClick={() => setImageFile(null)}
            style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1rem", color: "#d32f2f" }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Input bar */}
      <form onSubmit={handleTextSubmit} style={inputBarStyle}>
        <button
          type="button"
          title="फोटो भेजें"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          style={iconBtnStyle(loading)}
        >
          📷
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          style={{ display: "none" }}
          onChange={handleImageChange}
        />

        <input
          type="text"
          placeholder="यहाँ टाइप करें…"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={loading}
          style={textInputStyle}
        />

        <VoiceInput
          onAudioReady={handleAudioReady}
          onTranscript={handleTranscript}
          disabled={loading}
        />

        <button
          type="submit"
          disabled={loading || (!inputText.trim() && !imageFile)}
          style={sendBtnStyle(loading, inputText, imageFile)}
        >
          ➤
        </button>
      </form>
    </div>
  );
}

// ── Styles ──────────────────────────────────────────────────────────────────

const welcomeContainerStyle = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  padding: 24,
  gap: 8,
  background: "linear-gradient(160deg, #e8f5e9 0%, #f0f9f0 50%, #e3f2fd 100%)",
};

const phoneInputStyle = {
  padding: "14px 18px",
  border: "2px solid #c8e6c9",
  borderRadius: 14,
  fontSize: "1.05rem",
  outline: "none",
  background: "#fff",
  transition: "border-color 0.2s",
};

const startBtnStyle = {
  padding: "14px",
  background: "linear-gradient(135deg, #1a6b3c, #2e7d32)",
  color: "#fff",
  border: "none",
  borderRadius: 14,
  fontSize: "1.05rem",
  fontWeight: 700,
  cursor: "pointer",
  boxShadow: "0 4px 12px rgba(26,107,60,0.3)",
  transition: "transform 0.1s",
};

const chatContainerStyle = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  maxWidth: 680,
  width: "100%",
  margin: "0 auto",
  background: "#e8f5e980",
  position: "relative",
};

const chatHeaderStyle = {
  background: "linear-gradient(135deg, rgba(26,107,60,0.9), rgba(46,125,50,0.9))",
  backdropFilter: "blur(10px)",
  WebkitBackdropFilter: "blur(10px)",
  color: "#fff",
  padding: "12px 18px",
  display: "flex",
  alignItems: "center",
  gap: 12,
  boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
  position: "sticky",
  top: 0,
  zIndex: 10,
};

const avatarStyle = {
  width: 40,
  height: 40,
  borderRadius: "50%",
  background: "rgba(255,255,255,0.2)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: "1.2rem",
};

const domainDotStyle = (color) => ({
  width: 8,
  height: 8,
  borderRadius: "50%",
  background: color,
  display: "inline-block",
  boxShadow: `0 0 4px ${color}`,
});

const messagesAreaStyle = {
  flex: 1,
  overflowY: "auto",
  padding: "16px 14px",
  display: "flex",
  flexDirection: "column",
  background: "linear-gradient(180deg, #f0f9f0 0%, #e8f5e9 100%)",
};

const emptyStateStyle = {
  textAlign: "center",
  marginTop: 40,
  padding: "0 20px",
};

const loadingBubbleStyle = {
  background: "#fff",
  borderRadius: "18px 18px 18px 4px",
  padding: "10px 16px",
  boxShadow: "0 1px 4px rgba(0,0,0,0.1)",
  display: "flex",
  alignItems: "center",
  gap: 4,
};

const dotAnimStyle = (delay) => ({
  animation: `blink 1s step-start ${delay}s infinite`,
  fontSize: "0.7rem",
  color: "#1a6b3c",
});

const imagePreviewStyle = {
  background: "#fff",
  borderTop: "1px solid #c8e6c9",
  padding: "10px 14px",
  display: "flex",
  alignItems: "center",
  gap: 12,
};

const inputBarStyle = {
  background: "rgba(255,255,255,0.85)",
  backdropFilter: "blur(8px)",
  WebkitBackdropFilter: "blur(8px)",
  borderTop: "1px solid rgba(200,230,201,0.5)",
  padding: "10px 12px",
  display: "flex",
  gap: 8,
  alignItems: "center",
  boxShadow: "0 -4px 12px rgba(0,0,0,0.03)",
  position: "sticky",
  bottom: 0,
};

const iconBtnStyle = (loading) => ({
  flexShrink: 0,
  background: "none",
  border: "none",
  cursor: loading ? "not-allowed" : "pointer",
  fontSize: "1.3rem",
  padding: "4px",
  opacity: loading ? 0.4 : 1,
  transition: "opacity 0.2s",
});

const textInputStyle = {
  flex: 1,
  border: "1.5px solid #e0e0e0",
  borderRadius: 22,
  padding: "10px 18px",
  fontSize: "0.95rem",
  outline: "none",
  background: "#fafafa",
  transition: "border-color 0.2s",
};

const sendBtnStyle = (loading, inputText, imageFile) => ({
  flexShrink: 0,
  width: 44,
  height: 44,
  borderRadius: "50%",
  border: "none",
  background:
    loading || (!inputText?.trim() && !imageFile)
      ? "#e0e0e0"
      : "linear-gradient(135deg, #1a6b3c, #2e7d32)",
  color: "#fff",
  fontSize: "1.1rem",
  cursor:
    loading || (!inputText?.trim() && !imageFile)
      ? "not-allowed"
      : "pointer",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  boxShadow: "0 4px 10px rgba(26,107,60,0.2)",
  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
  transform: loading ? "scale(0.95)" : "scale(1)",
});
