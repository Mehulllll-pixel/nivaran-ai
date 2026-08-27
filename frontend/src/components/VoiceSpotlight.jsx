import { useState, useRef } from "react";
import { Mic, Bot, Calendar, Volume2, Play, Pause, ArrowRight, ExternalLink, Sparkles } from "lucide-react";

export function VoiceSpotlight({ events, onInspectCase }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  const heroEvent = (events || []).find((e) => e.customer_id === "cust_hero_demo");

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
  };

  return (
    <div
      id="voice-recovery-spotlight"
      style={{
        background: "linear-gradient(180deg, #141727 0%, #0d0f18 100%)",
        border: "1px solid rgba(99, 102, 241, 0.3)",
        borderRadius: "14px",
        padding: "20px 24px",
        marginBottom: "20px",
        boxShadow: "0 8px 32px -4px rgba(0, 0, 0, 0.5), inset 0 1px 0 0 rgba(255, 255, 255, 0.1)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Subtle top glowing line */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "2px",
          background: "linear-gradient(90deg, transparent 0%, #6366f1 30%, #a855f7 70%, transparent 100%)",
        }}
      />

      {/* Header bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "16px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              background: "rgba(99, 102, 241, 0.15)",
              border: "1px solid rgba(99, 102, 241, 0.4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#818cf8",
            }}
          >
            <Sparkles size={18} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "#f3f4f6", letterSpacing: "-0.01em" }}>
                Voice Recovery Spotlight
              </h3>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  padding: "2px 8px",
                  borderRadius: "12px",
                  background: "rgba(99, 102, 241, 0.2)",
                  color: "#a5b4fc",
                  border: "1px solid rgba(99, 102, 241, 0.4)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                HERO DEMO CASE
              </span>
            </div>
            <p style={{ margin: "2px 0 0", fontSize: "12px", color: "var(--text-secondary)" }}>
              Hinglish Voice Recovery Loop · Customer{" "}
              <span className="font-mono" style={{ color: "#e2e8f0", fontWeight: 600 }}>cust_hero_demo</span> ·{" "}
              <span className="font-mono" style={{ color: "var(--status-success)", fontWeight: 600 }}>₹12,000.00 Recovered</span>
            </p>
          </div>
        </div>

        {heroEvent && onInspectCase && (
          <button
            onClick={() => onInspectCase(heroEvent.id)}
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              borderRadius: "8px",
              color: "#e2e8f0",
              padding: "7px 12px",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(99, 102, 241, 0.2)";
              e.currentTarget.style.borderColor = "rgba(99, 102, 241, 0.4)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.12)";
            }}
          >
            <span>Inspect Full Audit Trail</span>
            <ExternalLink size={13} />
          </button>
        )}
      </div>

      {/* 4-Step Horizontal Stepper / Flow */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
          gap: "12px",
          position: "relative",
        }}
      >
        {/* Step 1: Customer Voice Input */}
        <div
          style={{
            background: "#0c0e15",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "10px",
            padding: "14px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
              <div
                style={{
                  width: "22px",
                  height: "22px",
                  borderRadius: "6px",
                  background: "rgba(59, 130, 246, 0.15)",
                  color: "#60a5fa",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Mic size={13} />
              </div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                1. Voice Call Received
              </span>
            </div>
            <div
              style={{
                fontSize: "12px",
                color: "#e2e8f0",
                fontStyle: "italic",
                lineHeight: "1.4",
                background: "rgba(0, 0, 0, 0.3)",
                padding: "8px 10px",
                borderRadius: "6px",
                borderLeft: "2px solid #3b82f6",
              }}
            >
              "Bhai abhi paise nahi hai, kal salary aayegi, kal kar dunga"
            </div>
          </div>
          <div style={{ marginTop: "10px", fontSize: "11px", color: "#64748b" }}>
            Demo transcript (pre-recorded customer response)
          </div>
        </div>

        {/* Step 2: Groq NLU Extraction */}
        <div
          style={{
            background: "#0c0e15",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "10px",
            padding: "14px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
              <div
                style={{
                  width: "22px",
                  height: "22px",
                  borderRadius: "6px",
                  background: "rgba(168, 85, 247, 0.15)",
                  color: "#c084fc",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Bot size={13} />
              </div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                2. NLU Intent Extracted
              </span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px" }}>
                <span style={{ color: "#94a3b8" }}>Intent:</span>
                <span
                  className="font-mono"
                  style={{
                    color: "#c084fc",
                    fontWeight: 600,
                    background: "rgba(168, 85, 247, 0.12)",
                    padding: "2px 6px",
                    borderRadius: "4px",
                  }}
                >
                  promise_future_payment
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px" }}>
                <span style={{ color: "#94a3b8" }}>Model:</span>
                <span className="font-mono" style={{ color: "#34d399", fontWeight: 600, fontSize: "10px" }}>
                  openai/gpt-oss-20b (Groq)
                </span>
              </div>
            </div>
          </div>
          <div style={{ marginTop: "10px", fontSize: "11px", color: "#64748b" }}>
            Confidence: <span className="font-mono" style={{ color: "#34d399", fontWeight: 600 }}>high</span> · Structured JSON Schema
          </div>
        </div>

        {/* Step 3: Guardrail & Promise Resolution */}
        <div
          style={{
            background: "#0c0e15",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "10px",
            padding: "14px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
              <div
                style={{
                  width: "22px",
                  height: "22px",
                  borderRadius: "6px",
                  background: "rgba(245, 158, 11, 0.15)",
                  color: "#fbbf24",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Calendar size={13} />
              </div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                3. Promise Resolved
              </span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px" }}>
                <span style={{ color: "#94a3b8" }}>Customer stated:</span>
                <span className="font-mono" style={{ color: "#94a3b8", fontStyle: "italic" }}>none</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", fontSize: "11px" }}>
                <span style={{ color: "#94a3b8" }}>Applied amount:</span>
                <div style={{ textAlign: "right" }}>
                  <span className="font-mono" style={{ color: "#fbbf24", fontWeight: 700 }}>₹12,000.00</span>
                  <div style={{ fontSize: "9px", color: "#d97706", lineHeight: "1.2" }}>
                    (inferred from balance, Rule 8)
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px", marginTop: "2px" }}>
                <span style={{ color: "#94a3b8" }}>Target Date:</span>
                <span className="font-mono" style={{ color: "#e2e8f0" }}>kal (Tomorrow)</span>
              </div>
            </div>
          </div>
          <div style={{ marginTop: "8px", fontSize: "11px", color: "#64748b" }}>
            Guardrail: <span className="font-mono" style={{ color: "#a5b4fc" }}>schedule_follow_up</span>
          </div>
        </div>

        {/* Step 4: Sarvam AI Voice TTS Audio */}
        <div
          style={{
            background: "linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(16, 185, 129, 0.08) 100%)",
            border: "1px solid rgba(99, 102, 241, 0.4)",
            borderRadius: "10px",
            padding: "14px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <div
                  style={{
                    width: "22px",
                    height: "22px",
                    borderRadius: "6px",
                    background: "rgba(16, 185, 129, 0.2)",
                    color: "#34d399",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Volume2 size={13} />
                </div>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "#34d399", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                  4. Agent Audio Response
                </span>
              </div>
            </div>
            
            <div
              style={{
                fontSize: "11px",
                color: "#e2e8f0",
                fontStyle: "italic",
                lineHeight: "1.35",
                marginBottom: "8px",
              }}
            >
              "Theek hai sir, hum aapke 12000 rupaye kal ke liye note kar lete hain. Dhanyawaad!"
            </div>

            {/* Hidden audio element for programmatic or custom controls */}
            <audio
              ref={audioRef}
              src="/hero-demo-response.mp3"
              onEnded={handleAudioEnded}
              preload="auto"
            />

            {/* Quick Play Button */}
            <button
              onClick={togglePlay}
              style={{
                width: "100%",
                background: isPlaying
                  ? "linear-gradient(135deg, #10b981 0%, #059669 100%)"
                  : "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                padding: "6px 10px",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "6px",
                boxShadow: isPlaying
                  ? "0 0 12px rgba(16, 185, 129, 0.4)"
                  : "0 0 12px rgba(99, 102, 241, 0.3)",
                transition: "all 0.2s ease",
              }}
            >
              {isPlaying ? <Pause size={13} /> : <Play size={13} />}
              <span>{isPlaying ? "Pause Agent Audio" : "Play Agent Voice (Sarvam)"}</span>
            </button>
          </div>
          <div style={{ marginTop: "8px", fontSize: "10px", color: "#94a3b8", display: "flex", justifyContent: "space-between" }}>
            <span>Sarvam Bulbul v3 (Pre-generated)</span>
            <span className="font-mono">5.29s MP3</span>
          </div>
        </div>
      </div>
    </div>
  );
}
