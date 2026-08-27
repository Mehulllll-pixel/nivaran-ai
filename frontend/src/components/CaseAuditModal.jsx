import { useEffect, useState } from "react";
import { fetchCaseTimeline } from "../api";
import { X, Volume2, ShieldCheck, CheckCircle2, AlertTriangle, AlertCircle, Clock } from "lucide-react";

export function CaseAuditModal({ eventId, onClose }) {
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!eventId) return;
    setLoading(true);
    fetchCaseTimeline(eventId)
      .then((data) => {
        setCaseData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [eventId]);

  if (!eventId) return null;

  const formatINR = (val) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(val || 0);
  };

  const getStatusBadge = (status) => {
    const s = (status || "").toLowerCase();
    if (s === "recovered") {
      return {
        bg: "rgba(16, 185, 129, 0.12)",
        text: "#34d399",
        border: "rgba(16, 185, 129, 0.3)",
        label: "RECOVERED",
      };
    }
    if (s === "stopped") {
      return {
        bg: "rgba(168, 85, 247, 0.12)",
        text: "#c084fc",
        border: "rgba(168, 85, 247, 0.3)",
        label: "STOPPED (COMPLIANCE)",
      };
    }
    if (s === "pending") {
      return {
        bg: "rgba(245, 158, 11, 0.12)",
        text: "#fbbf24",
        border: "rgba(245, 158, 11, 0.3)",
        label: "PENDING",
      };
    }
    return {
      bg: "rgba(239, 68, 68, 0.12)",
      text: "#f87171",
      border: "rgba(239, 68, 68, 0.3)",
      label: "FAILED",
    };
  };

  // Group decisions with their actions and outcomes
  const attempts = (caseData?.decisions || []).map((decision) => {
    const action = (caseData?.actions || []).find((a) => a.decision_id === decision.id);
    const outcome = action
      ? (caseData?.outcomes || []).find((o) => o.action_id === action.id)
      : null;
    return { decision, action, outcome };
  });

  const hasStopped = attempts.some(
    (a) => a.outcome?.status === "stopped" || a.decision?.chosen_action === "stopped"
  );

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(3, 4, 8, 0.8)",
        backdropFilter: "blur(6px)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1000,
        padding: "20px",
        animation: "fadeIn 0.2s ease-out",
      }}
      onClick={onClose}
    >
      <div
        id="case-audit-modal"
        style={{
          background: "#11131c",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "760px",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "28px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 30px rgba(99, 102, 241, 0.1)",
          position: "relative",
          color: "#f3f4f6",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
              <h2 style={{ margin: 0, fontSize: "18px", fontWeight: 700, color: "#f3f4f6", letterSpacing: "-0.01em" }}>
                Case Audit Trail & Decision Logs
              </h2>
              {hasStopped && (
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    padding: "3px 8px",
                    borderRadius: "12px",
                    background: "rgba(168, 85, 247, 0.15)",
                    color: "#c084fc",
                    border: "1px solid rgba(168, 85, 247, 0.3)",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                >
                  <ShieldCheck size={12} />
                  <span>STOPPED BY COMPLIANCE CAP</span>
                </span>
              )}
            </div>
            <p style={{ margin: 0, fontSize: "12px", color: "var(--text-secondary)" }}>
              Event UUID: <span className="font-mono" style={{ color: "#a5b4fc" }}>{eventId}</span>
            </p>
          </div>
          <button
            id="close-modal-btn"
            onClick={onClose}
            style={{
              background: "rgba(255, 255, 255, 0.06)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              padding: "6px 10px",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 600,
              color: "#9ca3af",
              display: "flex",
              alignItems: "center",
              gap: "4px",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.12)";
              e.currentTarget.style.color = "#ffffff";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.06)";
              e.currentTarget.style.color = "#9ca3af";
            }}
          >
            <X size={14} />
            <span>Close</span>
          </button>
        </div>

        {loading && <p style={{ color: "var(--text-secondary)" }}>Loading audit timeline...</p>}
        {error && <p style={{ color: "var(--status-risk)" }}>Error: {error}</p>}

        {caseData && (
          <div>
            {/* Event Summary Card */}
            <div
              style={{
                background: "#0c0e15",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "12px",
                padding: "16px",
                marginBottom: "20px",
              }}
            >
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "12px" }}>
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>Customer</div>
                  <div className="font-mono" style={{ fontSize: "13px", fontWeight: 600, color: "#f3f4f6" }}>
                    {caseData.event.customer_id}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>Amount at Risk</div>
                  <div className="font-mono" style={{ fontSize: "14px", fontWeight: 700, color: "#f87171" }}>
                    {formatINR(caseData.event.amount)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>Event Type</div>
                  <div style={{ fontSize: "12px", fontWeight: 600, color: "#e2e8f0" }}>
                    {caseData.event.event_type}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>Raw Signal &rarr; Root Cause</div>
                  <div style={{ fontSize: "12px", fontWeight: 500, color: "#e2e8f0" }}>
                    {caseData.event.raw_reason_code ? (
                      <>
                        <span style={{ color: "#94a3b8" }}>{caseData.event.raw_reason_code}</span>
                        <span style={{ color: "#6366f1", margin: "0 5px" }}>&rarr;</span>
                        <span style={{ color: "#818cf8", fontWeight: 600 }}>{caseData.decisions?.[0]?.root_cause || "unknown"}</span>
                      </>
                    ) : (
                      <>
                        <span style={{ color: "#94a3b8" }}>{caseData.event.event_type}</span>
                        <span style={{ color: "#6366f1", margin: "0 5px" }}>&rarr;</span>
                        <span style={{ color: "#818cf8", fontWeight: 600 }}>{caseData.decisions?.[0]?.root_cause || "unknown"}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>


              {/* Transcript / Resolution context block — always shown, content depends on whether voice was reached */}
              {(() => {
                const voiceAction = (caseData?.actions || []).find(
                  (a) => a.action_type === "voice_call_hinglish"
                );
                const voiceDecision = voiceAction
                  ? (caseData?.decisions || []).find((d) => d.id === voiceAction.decision_id)
                  : null;

                if (voiceAction) {
                  // Voice was reached — show the transcript that was actually fed to the NLU pipeline
                  return caseData.event.demo_transcript ? (
                    <div
                      style={{
                        background: "rgba(255, 255, 255, 0.03)",
                        border: "1px dashed rgba(99, 102, 241, 0.3)",
                        borderRadius: "8px",
                        padding: "10px 14px",
                        marginTop: "8px",
                      }}
                    >
                      <div style={{ fontSize: "11px", fontWeight: 600, color: "#a5b4fc", marginBottom: "3px" }}>
                        Customer Transcript (fed to NLU pipeline on attempt #{voiceDecision?.attempt_number}):
                      </div>
                      <div style={{ fontSize: "13px", color: "#f1f5f9", fontStyle: "italic" }}>
                        &ldquo;{caseData.event.demo_transcript}&rdquo;
                      </div>
                    </div>
                  ) : null;
                } else {
                  // Voice was never reached — show an honest explanation
                  const lastAttempt = attempts[attempts.length - 1];
                  const resolvedAction = lastAttempt?.action?.action_type || lastAttempt?.decision?.chosen_action || "automated action";
                  const resolvedAttemptNum = lastAttempt?.decision?.attempt_number ?? "?";
                  return (
                    <div
                      style={{
                        background: "rgba(245, 158, 11, 0.04)",
                        border: "1px dashed rgba(245, 158, 11, 0.2)",
                        borderRadius: "8px",
                        padding: "10px 14px",
                        marginTop: "8px",
                        display: "flex",
                        alignItems: "flex-start",
                        gap: "8px",
                      }}
                    >
                      <Clock size={13} style={{ color: "#fbbf24", marginTop: "2px", flexShrink: 0 }} />
                      <div>
                        <div style={{ fontSize: "11px", fontWeight: 600, color: "#fbbf24", marginBottom: "2px" }}>
                          No voice interaction occurred
                        </div>
                        <div style={{ fontSize: "12px", color: "#94a3b8", lineHeight: "1.5" }}>
                          Resolved via <span style={{ fontFamily: "monospace", color: "#e2e8f0" }}>{resolvedAction}</span> on attempt {resolvedAttemptNum} — the pipeline did not reach{" "}
                          <span style={{ fontFamily: "monospace", color: "#e2e8f0" }}>voice_call_hinglish</span>, so no customer transcript was processed by the NLU pipeline.
                        </div>
                      </div>
                    </div>
                  );
                }
              })()}

            </div>

            {/* Chronological Timeline */}
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "#f3f4f6", marginBottom: "14px", letterSpacing: "-0.01em" }}>
              Intervention History & Decision Engine Steps
            </h3>

            {attempts.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>No attempts processed for this event yet.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                {attempts.map(({ decision, action, outcome }, index) => {
                  const badge = outcome ? getStatusBadge(outcome.status) : null;
                  const isStopped = decision.chosen_action === "stopped";

                  return (
                    <div
                      key={decision.id || index}
                      style={{
                        border: isStopped
                          ? "1px solid rgba(168, 85, 247, 0.4)"
                          : "1px solid rgba(255, 255, 255, 0.08)",
                        borderRadius: "12px",
                        padding: "16px",
                        background: isStopped ? "rgba(168, 85, 247, 0.05)" : "#0c0e15",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
                      }}
                    >
                      {/* Attempt Header */}
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "10px",
                          borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
                          paddingBottom: "8px",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span
                            className="font-mono"
                            style={{
                              background: "rgba(99, 102, 241, 0.2)",
                              color: "#a5b4fc",
                              border: "1px solid rgba(99, 102, 241, 0.4)",
                              fontSize: "11px",
                              fontWeight: 700,
                              borderRadius: "6px",
                              padding: "2px 6px",
                            }}
                          >
                            Attempt #{decision.attempt_number}
                          </span>
                          <span style={{ fontSize: "13px", fontWeight: 700, color: "#f3f4f6" }}>
                            {decision.chosen_action.toUpperCase()}
                          </span>
                        </div>
                        {badge && (
                          <span
                            style={{
                              fontSize: "11px",
                              fontWeight: 700,
                              padding: "3px 8px",
                              borderRadius: "8px",
                              background: badge.bg,
                              color: badge.text,
                              border: `1px solid ${badge.border}`,
                            }}
                          >
                            {badge.label}
                          </span>
                        )}
                      </div>

                      {/* Decision Reasoning */}
                      <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginBottom: "10px", lineHeight: "1.5" }}>
                        <strong style={{ color: "#d1d5db" }}>Decision Reasoning:</strong> {decision.reasoning}
                      </div>

                      {/* Action Execution & Notes */}
                      {action && (
                        <div
                          style={{
                            background: isStopped ? "rgba(168, 85, 247, 0.08)" : "rgba(255, 255, 255, 0.03)",
                            border: "1px solid rgba(255, 255, 255, 0.06)",
                            borderRadius: "8px",
                            padding: "10px 12px",
                            fontSize: "12px",
                            color: "#cbd5e1",
                            marginBottom: "10px",
                          }}
                        >
                          <div style={{ fontWeight: 600, color: "#94a3b8", marginBottom: "4px" }}>
                            Action Execution Details:
                          </div>
                          <div style={{ wordBreak: "break-word", lineHeight: "1.5" }}>
                            {action.notes || "No execution notes recorded."}
                          </div>
                        </div>
                      )}

                      {/* Hero Demo Voice Call Audio Playback (Sarvam AI TTS) */}
                      {caseData?.event?.customer_id === "cust_hero_demo" &&
                        (decision?.chosen_action === "voice_call_hinglish" || action?.action_type === "voice_call_hinglish") && (
                          <div
                            id="hero-audio-player-container"
                            style={{
                              background: "linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(16, 185, 129, 0.1) 100%)",
                              border: "1px solid rgba(99, 102, 241, 0.4)",
                              borderRadius: "10px",
                              padding: "12px 14px",
                              marginBottom: "10px",
                              display: "flex",
                              flexDirection: "column",
                              gap: "8px",
                            }}
                          >
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                              <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", fontWeight: 700, color: "#a5b4fc" }}>
                                <Volume2 size={15} color="#34d399" />
                                <span>Agent Spoken Response (Sarvam AI Voice)</span>
                              </div>
                              <span
                                style={{
                                  fontSize: "11px",
                                  color: "#34d399",
                                  background: "rgba(16, 185, 129, 0.15)",
                                  border: "1px solid rgba(16, 185, 129, 0.3)",
                                  padding: "2px 8px",
                                  borderRadius: "10px",
                                  fontWeight: 600,
                                }}
                              >
                                ₹12,000 Promise Confirmed
                              </span>
                            </div>
                            <div style={{ fontSize: "12px", color: "#e2e8f0", fontStyle: "italic" }}>
                              "Theek hai sir, hum aapke 12000 rupaye kal ke liye note kar lete hain. Dhanyawaad!"
                            </div>
                            <audio
                              id="hero-demo-audio-player"
                              controls
                              src="/hero-demo-response.mp3"
                              style={{ width: "100%", height: "32px" }}
                            >
                              Your browser does not support the audio element.
                            </audio>
                          </div>
                        )}

                      {/* Outcome Details */}
                      {outcome && (
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
                          <span>
                            Amount Recovered:{" "}
                            <strong className="font-mono" style={{ color: outcome.amount_recovered > 0 ? "var(--status-success)" : "var(--text-muted)" }}>
                              {formatINR(outcome.amount_recovered)}
                            </strong>
                          </span>
                          <span className="font-mono" style={{ fontSize: "11px" }}>
                            Resolved: {new Date(outcome.resolved_at).toLocaleString()}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
