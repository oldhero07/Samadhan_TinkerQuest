import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error("[ErrorBoundary]", error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          flex: 1, display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          padding: 24, gap: 12, textAlign: "center",
          background: "linear-gradient(160deg, #e8f5e9 0%, #f0f9f0 100%)"
        }}>
          <div style={{ fontSize: "3rem" }}>⚠️</div>
          <h3 style={{ color: "#c62828", margin: 0 }}>कुछ गड़बड़ हो गई</h3>
          <p style={{ color: "#666", maxWidth: 300 }}>
            पेज में कोई समस्या आई। कृपया रिफ्रेश करें।
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "10px 24px", background: "#1a6b3c", color: "#fff",
              border: "none", borderRadius: 10, cursor: "pointer",
              fontWeight: 700, fontSize: "1rem"
            }}
          >
            🔄 रिफ्रेश करें
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
