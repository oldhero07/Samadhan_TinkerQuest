import React from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import FarmerChat from "./pages/FarmerChat.jsx";
import PartnerView from "./pages/PartnerView.jsx";

function NavBar() {
  const { pathname } = useLocation();

  return (
    <nav style={navStyle}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: "1.4rem" }}>🌾</span>
        <span style={{ fontSize: "1.15rem", fontWeight: 800, letterSpacing: 0.5 }}>
          समाधान
        </span>
        <span style={{
          fontSize: "0.6rem",
          background: "rgba(255,255,255,0.2)",
          padding: "2px 6px",
          borderRadius: 6,
          marginLeft: 2,
          fontWeight: 600,
        }}>
          मित्र
        </span>
      </div>

      <div style={{ display: "flex", gap: 6 }}>
        <Link to="/" style={linkStyle(pathname === "/")}>
          💬 किसान चैट
        </Link>
        <Link to="/partner" style={linkStyle(pathname === "/partner")}>
          🤝 पार्टनर
        </Link>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <NavBar />
      <main style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <Routes>
          <Route path="/" element={<FarmerChat />} />
          <Route path="/partner" element={<PartnerView />} />
        </Routes>
      </main>
    </div>
  );
}

// ── Styles ──
const navStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  background: "linear-gradient(135deg, #1a6b3c, #1b5e30)",
  color: "#fff",
  padding: "10px 18px",
  boxShadow: "0 2px 10px rgba(0,0,0,0.2)",
  position: "sticky",
  top: 0,
  zIndex: 100,
};

const linkStyle = (active) => ({
  color: active ? "#fff" : "#c8e6c9",
  textDecoration: "none",
  fontWeight: active ? 700 : 500,
  fontSize: "0.85rem",
  padding: "6px 12px",
  borderRadius: 8,
  background: active ? "rgba(255,255,255,0.15)" : "transparent",
  transition: "all 0.2s",
});
