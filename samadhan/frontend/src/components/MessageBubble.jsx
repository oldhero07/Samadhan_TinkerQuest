import React from "react";

// Domain → badge styling
const DOMAIN_STYLES = {
  agriculture: { bg: "#e8f5e9", text: "#2e7d32", label: "🌾 कृषि", border: "#a5d6a7" },
  health: { bg: "#e3f2fd", text: "#1565c0", label: "🏥 स्वास्थ्य", border: "#90caf9" },
  schemes: { bg: "#fff3e0", text: "#e65100", label: "📋 योजना", border: "#ffcc80" },
  general: { bg: "#f5f5f5", text: "#555", label: "💬 सामान्य", border: "#e0e0e0" },
};

export default function MessageBubble({ message }) {
  const { role, text, domain, timestamp, image } = message;
  const isUser = role === "user";

  const domainMeta = domain ? DOMAIN_STYLES[domain] ?? DOMAIN_STYLES.general : null;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        marginBottom: 10,
        animation: "fadeSlideIn 0.3s ease-out",
      }}
    >
      {/* Image preview (user crop photos) */}
      {image && (
        <img
          src={image}
          alt="crop photo"
          style={{
            maxWidth: 200,
            borderRadius: 14,
            marginBottom: 4,
            border: "2px solid #c8e6c9",
            alignSelf: isUser ? "flex-end" : "flex-start",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          }}
        />
      )}

      {/* Message bubble */}
      <div
        style={{
          maxWidth: "80%",
          padding: "10px 14px",
          borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
          background: isUser
            ? "linear-gradient(135deg, #1a6b3c, #2e7d32)"
            : "#fff",
          color: isUser ? "#fff" : "#1a1a1a",
          boxShadow: isUser
            ? "0 2px 8px rgba(26,107,60,0.3)"
            : "0 1px 4px rgba(0,0,0,0.1)",
          fontSize: "0.97rem",
          lineHeight: 1.6,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {text}
      </div>

      {/* Bottom row: domain badge + timestamp */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          marginTop: 3,
          flexDirection: isUser ? "row-reverse" : "row",
        }}
      >
        {domainMeta && !isUser && (
          <span
            style={{
              fontSize: "0.68rem",
              fontWeight: 600,
              padding: "2px 8px",
              borderRadius: 10,
              background: domainMeta.bg,
              color: domainMeta.text,
              border: `1px solid ${domainMeta.border}`,
            }}
          >
            {domainMeta.label}
          </span>
        )}
        <span style={{ fontSize: "0.65rem", color: "#999" }}>
          {timestamp}
        </span>
      </div>

      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
