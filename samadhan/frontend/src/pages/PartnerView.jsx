import React, { useState, useCallback } from "react";

const API_BASE = "/api";
const PARTNER_HEADERS = { "X-Partner-Token": "samadhan2026" };

// Domain color mapping
const DOMAIN_COLORS = {
  agriculture: { bg: "#e8f5e9", border: "#4caf50", text: "#2e7d32", icon: "🌾" },
  health: { bg: "#e3f2fd", border: "#2196f3", text: "#1565c0", icon: "🏥" },
  schemes: { bg: "#fff3e0", border: "#ff9800", text: "#e65100", icon: "📋" },
  general: { bg: "#f5f5f5", border: "#9e9e9e", text: "#555", icon: "💬" },
};

const STATUS_BADGES = {
  resolved: { bg: "#e8f5e9", text: "#2e7d32", label: "✅ हल" },
  unresolved: { bg: "#ffebee", text: "#c62828", label: "⚠️ अनसुलझा" },
  follow_up_needed: { bg: "#fff3e0", text: "#e65100", label: "🔄 फॉलो-अप" },
  active: { bg: "#e3f2fd", text: "#1565c0", label: "🔵 सक्रिय" },
};

function TimelineEntry({ entry }) {
  const domain = DOMAIN_COLORS[entry.domain] || DOMAIN_COLORS.general;
  const status = STATUS_BADGES[entry.status] || STATUS_BADGES.active;

  return (
    <div style={{
      display: "flex", gap: 14, padding: "14px 0",
      borderBottom: "1px solid #f0f0f0",
    }}>
      {/* Domain icon */}
      <div style={{
        width: 42, height: 42, borderRadius: 12,
        background: domain.bg, border: `2px solid ${domain.border}`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: "1.2rem", flexShrink: 0,
      }}>
        {domain.icon}
      </div>
      {/* Content */}
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
          <span style={{ fontSize: "0.75rem", color: "#888", fontWeight: 600 }}>
            {entry.date}
          </span>
          <span style={{
            fontSize: "0.68rem", fontWeight: 600, padding: "2px 8px",
            borderRadius: 10, background: status.bg, color: status.text,
          }}>
            {status.label}
          </span>
        </div>
        <div style={{ fontSize: "0.92rem", color: "#333", lineHeight: 1.5 }}>
          {entry.summary}
        </div>
      </div>
    </div>
  );
}

function QuickFact({ icon, label, value, valueColor }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "8px 0" }}>
      <span style={{ fontSize: "1rem", minWidth: 22, marginTop: 1 }}>{icon}</span>
      <div>
        <span style={{ fontSize: "0.7rem", color: "#888", fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>
          {label}
        </span>
        <div style={{ fontSize: "0.92rem", color: valueColor || "#222", marginTop: 2, lineHeight: 1.4 }}>
          {value || "—"}
        </div>
      </div>
    </div>
  );
}

function FlagItem({ flag }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      padding: "8px 12px", borderRadius: 10,
      background: "#ffebee", border: "1px solid #ffcdd2",
      fontSize: "0.85rem", color: "#c62828",
    }}>
      🚨 {flag.replace(/_/g, " ")}
    </div>
  );
}

function AggregateStats({ timeline, flags }) {
  const agCount = timeline.filter((e) => e.domain === "agriculture").length;
  const healthCount = timeline.filter((e) => e.domain === "health").length;
  const schemesCount = timeline.filter((e) => e.domain === "schemes").length;
  const resolvedCount = timeline.filter((e) => e.status === "resolved").length;

  return (
    <div style={{
      display: "flex", gap: 10, flexWrap: "wrap",
      background: "#fff", borderRadius: 14, padding: "14px 20px",
      boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
    }}>
      {[
        { icon: "🌾", label: "कृषि", count: agCount, color: "#2e7d32" },
        { icon: "🏥", label: "स्वास्थ्य", count: healthCount, color: "#1565c0" },
        { icon: "📋", label: "योजना", count: schemesCount, color: "#e65100" },
        { icon: "✅", label: "हल", count: resolvedCount, color: "#388e3c" },
        { icon: "🚨", label: "अलर्ट", count: flags.length, color: "#c62828" },
      ].map(({ icon, label, count, color }) => (
        <div key={label} style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 14px", borderRadius: 20, background: "#f5f5f5" }}>
          <span style={{ fontSize: "1rem" }}>{icon}</span>
          <span style={{ fontSize: "0.78rem", color: "#888" }}>{label}</span>
          <span style={{ fontWeight: 700, color, fontSize: "1rem" }}>{count}</span>
        </div>
      ))}
    </div>
  );
}

function ProfileCard({ profile, summary, summaryLoading, onFlag, flagged }) {
  const p = profile.profile || {};
  const ag = p.agriculture || {};
  const health = p.health || {};
  const schemes = p.schemes || {};
  const timeline = profile.timeline || [];
  const flags = profile.flags || [];

  return (
    <div style={{ maxWidth: 720, width: "100%", display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Header */}
      <div style={{
        background: "linear-gradient(135deg, #1a6b3c, #2e7d32)",
        borderRadius: 16, padding: "20px 24px", color: "#fff",
        boxShadow: "0 4px 16px rgba(26,107,60,0.25)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{
            width: 56, height: 56, borderRadius: "50%",
            background: "rgba(255,255,255,0.2)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "1.6rem",
          }}>
            👨‍🌾
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 800, fontSize: "1.3rem" }}>
              {profile.name || profile.phone}
            </div>
            <div style={{ opacity: 0.85, fontSize: "0.85rem" }}>
              📍 {profile.village || "—"}, {profile.district || "—"} · 📱 {profile.phone}
            </div>
            <div style={{ opacity: 0.7, fontSize: "0.75rem", marginTop: 2 }}>
              पंजीकृत: {profile.registered_date || "—"}
            </div>
          </div>
          <button
            onClick={onFlag}
            style={{
              background: flagged ? "#e8f5e9" : "rgba(255,255,255,0.15)",
              border: "none", borderRadius: 10, padding: "8px 14px",
              color: flagged ? "#2e7d32" : "#fff", cursor: "pointer",
              fontWeight: 700, fontSize: "0.82rem", whiteSpace: "nowrap",
              boxShadow: "0 1px 4px rgba(0,0,0,0.15)",
            }}
          >
            {flagged ? "✅ फ्लैग किया" : "🚩 फॉलो-अप फ्लैग"}
          </button>
        </div>
      </div>

      {/* Aggregate Stats */}
      <AggregateStats timeline={timeline} flags={flags} />

      {/* AI Summary Card */}
      <div style={{
        background: "#fff", borderRadius: 14, padding: "18px 20px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
        borderLeft: "4px solid #1a6b3c",
      }}>
        <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#1a6b3c", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>
          🤖 AI सारांश
        </div>
        {summaryLoading ? (
          <div style={{ color: "#888", fontSize: "0.9rem" }}>सारांश तैयार हो रहा है...</div>
        ) : (
          <div style={{ fontSize: "0.92rem", color: "#333", lineHeight: 1.7 }}>
            {summary || "सारांश उपलब्ध नहीं है।"}
          </div>
        )}
      </div>

      {/* Main content: Timeline + Sidebar */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        {/* Timeline */}
        <div style={{
          flex: "2 1 400px", background: "#fff", borderRadius: 14,
          padding: "18px 20px", boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
        }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#1a6b3c", marginBottom: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>
            📅 टाइमलाइन
          </div>
          {timeline.length === 0 ? (
            <div style={{ color: "#888", fontSize: "0.9rem" }}>कोई इंटरैक्शन नहीं।</div>
          ) : (
            timeline.map((entry, i) => <TimelineEntry key={i} entry={entry} />)
          )}
        </div>

        {/* Sidebar: Quick Facts + Flags */}
        <div style={{ flex: "1 1 240px", display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Quick Facts */}
          <div style={{
            background: "#fff", borderRadius: 14,
            padding: "18px 20px", boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
          }}>
            <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#1a6b3c", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>
              📊 त्वरित जानकारी
            </div>
            <QuickFact
              icon="🌾"
              label="फसलें"
              value={ag.primary_crops?.length ? ag.primary_crops.join(", ") : null}
            />
            <QuickFact icon="🏡" label="जमीन" value={ag.land_area} />
            <QuickFact icon="🌤" label="मौसम" value={ag.current_season} />
            <QuickFact
              icon="📋"
              label="योजनाएं"
              value={Object.entries(schemes).map(
                ([k, v]) => `${k}: ${v.status || "?"}`
              ).join(" · ") || null}
            />
            {health.family_queries?.length > 0 && (
              <QuickFact
                icon="🏥"
                label="स्वास्थ्य"
                value={health.family_queries.map(
                  (q) => `${q.member}: ${q.symptom} (${q.date})`
                ).join("; ")}
              />
            )}
          </div>

          {/* Flags */}
          {flags.length > 0 && (
            <div style={{
              background: "#fff", borderRadius: 14,
              padding: "18px 20px", boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
            }}>
              <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#c62828", marginBottom: 10, textTransform: "uppercase", letterSpacing: 0.5 }}>
                🚨 सक्रिय अलर्ट
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {flags.map((flag, i) => <FlagItem key={i} flag={flag} />)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PartnerView() {
  const [phone, setPhone] = useState("");
  const [profile, setProfile] = useState(null);
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState("");
  const [flagged, setFlagged] = useState(false);
  const [flagMsg, setFlagMsg] = useState("");

  const handleLookup = async (e) => {
    e.preventDefault();
    const cleaned = phone.replace(/\D/g, "");
    if (cleaned.length < 10) {
      setError("कम से कम 10 अंक का नंबर दर्ज करें।");
      return;
    }
    setError("");
    setProfile(null);
    setSummary("");
    setFlagged(false);
    setFlagMsg("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/profile/${cleaned}`, {
        headers: PARTNER_HEADERS,
      });
      if (res.status === 404) {
        setError("इस नंबर का कोई प्रोफाइल नहीं मिला।");
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const profileData = await res.json();
      setProfile(profileData);

      // Fetch AI summary
      setSummaryLoading(true);
      try {
        const sumRes = await fetch(`${API_BASE}/partner/${cleaned}/summary`, {
          headers: PARTNER_HEADERS,
        });
        if (sumRes.ok) {
          const sumData = await sumRes.json();
          setSummary(sumData.summary || "");
        }
      } catch (e) {
        console.error("Summary fetch failed:", e);
      } finally {
        setSummaryLoading(false);
      }
    } catch (err) {
      setError("सर्वर से कनेक्ट नहीं हो पाया। बाद में कोशिश करें।");
    } finally {
      setLoading(false);
    }
  };

  const handleFlag = useCallback(async () => {
    if (flagged || !profile) return;
    const cleaned = phone.replace(/\D/g, "");
    try {
      await fetch(`${API_BASE}/partner/${cleaned}/flag`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...PARTNER_HEADERS },
        body: JSON.stringify({ flag: "follow_up_needed" }),
      });
    } catch {
      // Optimistic update even on error
    }
    setFlagged(true);
    setFlagMsg("✅ फॉलो-अप के लिए फ्लैग किया गया।");
    setTimeout(() => setFlagMsg(""), 4000);
  }, [flagged, profile, phone]);

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 8 }}>
        <h2 style={{ color: "#1a6b3c", fontWeight: 800, fontSize: "1.3rem", marginBottom: 4 }}>
          🤝 पार्टनर डैशबोर्ड
        </h2>
        <p style={{ color: "#666", fontSize: "0.85rem", maxWidth: 400, margin: "0 auto" }}>
          ASHA वर्कर / कृषि मित्र / FPO — किसान का मोबाइल नंबर डालें
        </p>
      </div>

      {/* Search */}
      <form onSubmit={handleLookup} style={searchFormStyle}>
        <input
          type="tel"
          placeholder="🔍 किसान का मोबाइल नंबर (10 अंक)"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          style={searchInputStyle}
        />
        <button type="submit" disabled={loading} style={searchBtnStyle(loading)}>
          {loading ? "खोज रहे हैं…" : "खोजें"}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div style={errorStyle}>
          ⚠️ {error}
        </div>
      )}

      {/* Flag confirmation */}
      {flagMsg && (
        <div style={{ background: "#e8f5e9", color: "#2e7d32", padding: "10px 18px", borderRadius: 12, marginBottom: 12, fontSize: "0.9rem", maxWidth: 560, width: "100%", border: "1px solid #c8e6c9", fontWeight: 600 }}>
          {flagMsg}
        </div>
      )}

      {/* Profile */}
      {profile && (
        <ProfileCard
          profile={profile}
          summary={summary}
          summaryLoading={summaryLoading}
          onFlag={handleFlag}
          flagged={flagged}
        />
      )}

      {/* Better empty state when no search yet */}
      {!profile && !error && !loading && (
        <div style={{ textAlign: "center", marginTop: 32, color: "#aaa", maxWidth: 400 }}>
          <div style={{ fontSize: "2.5rem", marginBottom: 10 }}>🔍</div>
          <div style={{ fontWeight: 600, color: "#888", marginBottom: 6, fontSize: "1rem" }}>
            किसान की जानकारी खोजें
          </div>
          <div style={{ fontSize: "0.85rem", lineHeight: 1.7 }}>
            ऊपर मोबाइल नंबर डालकर किसी भी किसान का प्रोफाइल, AI सारांश और टाइमलाइन देखें।
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{ marginTop: 24, textAlign: "center", color: "#bbb", fontSize: "0.7rem" }}>
        समाधान मित्र · TinkerQuest 26 · IIT Roorkee
      </div>
    </div>
  );
}

// ── Styles ──
const containerStyle = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  padding: "24px 16px",
  background: "linear-gradient(160deg, #f5f5f5 0%, #e8f5e9 50%, #e3f2fd 100%)",
  minHeight: "100%",
};

const searchFormStyle = {
  display: "flex",
  gap: 10,
  marginBottom: 24,
  width: "100%",
  maxWidth: 560,
};

const searchInputStyle = {
  flex: 1,
  padding: "13px 18px",
  border: "2px solid #c8e6c9",
  borderRadius: 14,
  fontSize: "1rem",
  outline: "none",
  background: "#fff",
  transition: "border-color 0.2s",
};

const searchBtnStyle = (loading) => ({
  padding: "13px 24px",
  background: loading ? "#aaa" : "linear-gradient(135deg, #1a6b3c, #2e7d32)",
  color: "#fff",
  border: "none",
  borderRadius: 14,
  fontSize: "1rem",
  fontWeight: 700,
  cursor: loading ? "not-allowed" : "pointer",
  whiteSpace: "nowrap",
  boxShadow: loading ? "none" : "0 4px 12px rgba(26,107,60,0.25)",
});

const errorStyle = {
  background: "#ffebee",
  color: "#c62828",
  padding: "12px 18px",
  borderRadius: 12,
  marginBottom: 20,
  fontSize: "0.9rem",
  maxWidth: 560,
  width: "100%",
  border: "1px solid #ffcdd2",
};
