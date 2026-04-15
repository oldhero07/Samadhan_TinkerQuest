import React, { useState, useRef, useEffect, useCallback } from "react";

/**
 * VoiceInput — Record audio via MediaRecorder, send as base64 to backend for Groq Whisper.
 * Falls back to Web Speech API if MediaRecorder is not available.
 */
export default function VoiceInput({ onAudioReady, onTranscript, disabled }) {
  const [recording, setRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [micError, setMicError] = useState(null);
  const mediaRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const errorTimerRef = useRef(null);

  // Always-fresh refs — avoids stale closure issues with parent callbacks
  const onAudioReadyRef = useRef(onAudioReady);
  const onTranscriptRef = useRef(onTranscript);
  useEffect(() => { onAudioReadyRef.current = onAudioReady; }, [onAudioReady]);
  useEffect(() => { onTranscriptRef.current = onTranscript; }, [onTranscript]);

  const showError = useCallback((msg) => {
    clearTimeout(errorTimerRef.current);
    setMicError(msg);
    errorTimerRef.current = setTimeout(() => setMicError(null), 3000);
  }, []);

  const fallbackWebSpeech = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      showError("ब्राउज़र सपोर्ट नहीं करता");
      return;
    }

    const rec = new SR();
    rec.lang = "hi-IN";
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    rec.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      if (transcript) onTranscriptRef.current?.(transcript);
    };
    rec.onerror = (e) => {
      if (e.error === "not-allowed") showError("माइक्रोफोन की अनुमति दें");
      setRecording(false);
    };
    rec.onend = () => setRecording(false);

    try {
      rec.start();
      setRecording(true);
    } catch (e) {
      showError("माइक्रोफोन शुरू नहीं हो पाया");
    }
  }, [showError]);

  const startRecording = useCallback(async () => {
    if (disabled) return;

    // If MediaRecorder / getUserMedia not available, go straight to Web Speech
    if (!navigator.mediaDevices?.getUserMedia) {
      fallbackWebSpeech();
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "";

      const mediaRecorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        clearInterval(timerRef.current);
        setDuration(0);

        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result.split(",")[1];
          onAudioReadyRef.current?.(base64);
        };
        reader.readAsDataURL(blob);
      };

      mediaRecorder.start(250);
      mediaRef.current = mediaRecorder;
      setRecording(true);
      setDuration(0);

      timerRef.current = setInterval(() => {
        setDuration((d) => d + 1);
      }, 1000);

    } catch (err) {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        showError("माइक्रोफोन की अनुमति दें");
      } else {
        // Non-permission error (device busy, not found, etc.) — try Web Speech
        fallbackWebSpeech();
      }
    }
  }, [disabled, fallbackWebSpeech, showError]);

  const stopRecording = useCallback(() => {
    if (mediaRef.current && mediaRef.current.state === "recording") {
      mediaRef.current.stop();
    }
    setRecording(false);
  }, []);

  const toggle = () => {
    if (recording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const formatTime = (s) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, position: "relative" }}>
      {recording && (
        <span style={{
          fontSize: "0.72rem",
          color: "#d32f2f",
          fontWeight: 700,
          fontVariantNumeric: "tabular-nums",
          animation: "pulse-text 1s infinite",
        }}>
          🔴 {formatTime(duration)}
        </span>
      )}
      <button
        type="button"
        onClick={toggle}
        disabled={disabled}
        title={micError ?? (recording ? "रोकें" : "बोलें (हिंदी)")}
        style={{
          flexShrink: 0,
          width: 42,
          height: 42,
          borderRadius: "50%",
          border: "none",
          cursor: disabled ? "not-allowed" : "pointer",
          background: micError ? "#e65100" : recording ? "#d32f2f" : "#1a6b3c",
          color: "#fff",
          fontSize: "1.2rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: recording
            ? "0 0 0 4px rgba(211,47,47,0.3)"
            : "0 2px 6px rgba(0,0,0,0.2)",
          transition: "all 0.2s",
          animation: recording ? "pulse 1s ease-in-out infinite" : "none",
        }}
      >
        {recording ? "⏹" : "🎙"}
      </button>
      {micError && (
        <span style={{
          position: "absolute",
          bottom: 50,
          right: 0,
          background: "#e65100",
          color: "#fff",
          fontSize: "0.72rem",
          padding: "4px 10px",
          borderRadius: 8,
          whiteSpace: "nowrap",
          boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
          zIndex: 20,
        }}>
          {micError}
        </span>
      )}
      <style>{`
        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 0 4px rgba(211,47,47,0.3); }
          50% { box-shadow: 0 0 0 8px rgba(211,47,47,0.1); }
        }
        @keyframes pulse-text {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}
