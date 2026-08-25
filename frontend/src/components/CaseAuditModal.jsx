import { useEffect, useState } from "react";
import { fetchCaseTimeline } from "../api";

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
      return { bg: "#d1fae5", text: "#065f46", border: "#a7f3d0", label: "RECOVERED" };
    }
    if (s === "stopped") {
      return { bg: "#ede9fe", text: "#5b21b6", border: "#c4b5fd", label: "STOPPED (COMPLIANCE)" };
    }
    if (s === "pending") {
      return { bg: "#fef3c7", text: "#92400e", border: "#fde68a", label: "PENDING" };
    }
    return { bg: "#fee2e2", text: "#991b1b", border: "#fecaca", label: "FAILED" };
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
        backgroundColor: "rgba(0, 0, 0, 0.6)",
        backdropFilter: "blur(2px)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1000,
        padding: "20px",
      }}
      onClick={onClose}
    >
      <div
        id="case-audit-modal"
        style={{
          background: "#ffffff",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "760px",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "28px",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.2)",
          position: "relative",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#111827" }}>
                Case Audit Trail
              </h2>
              {hasStopped && (
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    padding: "3px 8px",
                    borderRadius: "12px",
                    background: "#ede9fe",
                    color: "#5b21b6",
                    border: "1px solid #c4b5fd",
                  }}
                >
                  STOPPED BY COMPLIANCE RULE
                </span>
              )}
            </div>
            <p style={{ margin: 0, fontSize: "12px", color: "#6b7280", fontFamily: "monospace" }}>
              Event ID: {eventId}
            </p>
          </div>
          <button
            id="close-modal-btn"
            onClick={onClose}
            style={{
              background: "#f3f4f6",
              border: "none",
              borderRadius: "8px",
              padding: "6px 12px",
              cursor: "pointer",
              fontSize: "14px",
              fontWeight: 600,
              color: "#4b5563",
            }}
          >
            ✕ Close
          </button>
        </div>

        {loading && <p style={{ color: "#6b7280" }}>Loading audit timeline...</p>}
        {error && <p style={{ color: "#ef4444" }}>Error: {error}</p>}

        {caseData && (
          <div>
            {/* Event Summary Card */}
            <div
              style={{
                background: "#f9fafb",
                border: "1px solid #e5e7eb",
                borderRadius: "12px",
                padding: "16px",
                marginBottom: "24px",
              }}
            >
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "12px" }}>
                <div>
                  <div style={{ fontSize: "11px", color: "#6b7280", textTransform: "uppercase" }}>Customer</div>
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "#111827" }}>
                    {caseData.event.customer_id}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "11px", color: "#6b7280", textTransform: "uppercase" }}>Amount at Risk</div>
                  <div style={{ fontSize: "14px", fontWeight: 700, color: "#ef4444" }}>
                    {formatINR(caseData.event.amount)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "11px", color: "#6b7280", textTransform: "uppercase" }}>Event Type / Reason</div>
                  <div style={{ fontSize: "13px", fontWeight: 500, color: "#374151" }}>
                    {caseData.event.event_type} {caseData.event.raw_reason_code ? `(${caseData.event.raw_reason_code})` : ""}
                  </div>
                </div>
              </div>

              {caseData.event.demo_transcript && (
                <div
                  style={{
                    background: "#ffffff",
                    border: "1px dashed #cbd5e1",
                    borderRadius: "8px",
                    padding: "10px 14px",
                    marginTop: "8px",
                  }}
                >
                  <div style={{ fontSize: "11px", fontWeight: 600, color: "#475569", marginBottom: "3px" }}>
                    Assigned Customer Hinglish Response:
                  </div>
                  <div style={{ fontSize: "13px", color: "#1e293b", fontStyle: "italic" }}>
                    "{caseData.event.demo_transcript}"
                  </div>
                </div>
              )}
            </div>

            {/* Chronological Timeline */}
            <h3 style={{ fontSize: "15px", fontWeight: 600, color: "#111827", marginBottom: "16px" }}>
              Intervention History & Decision Engine Steps
            </h3>

            {attempts.length === 0 ? (
              <p style={{ color: "#9ca3af", fontSize: "13px" }}>No attempts processed for this event yet.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {attempts.map(({ decision, action, outcome }, index) => {
                  const badge = outcome ? getStatusBadge(outcome.status) : null;
                  const isStopped = decision.chosen_action === "stopped";

                  return (
                    <div
                      key={decision.id || index}
                      style={{
                        border: isStopped ? "1.5px solid #c4b5fd" : "1px solid #e5e7eb",
                        borderRadius: "12px",
                        padding: "16px",
                        background: isStopped ? "#faf5ff" : "#ffffff",
                        boxShadow: "0 1px 2px rgba(0,0,0,0.03)",
                      }}
                    >
                      {/* Attempt Header */}
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "10px",
                          borderBottom: "1px solid #f3f4f6",
                          paddingBottom: "8px",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span
                            style={{
                              background: "#3b82f6",
                              color: "#fff",
                              fontSize: "11px",
                              fontWeight: 700,
                              borderRadius: "6px",
                              padding: "2px 6px",
                            }}
                          >
                            Attempt #{decision.attempt_number}
                          </span>
                          <span style={{ fontSize: "14px", fontWeight: 600, color: "#111827" }}>
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
                      <div style={{ fontSize: "13px", color: "#4b5563", marginBottom: "10px" }}>
                        <strong>Decision Reasoning:</strong> {decision.reasoning}
                      </div>

                      {/* Action Execution & Notes */}
                      {action && (
                        <div
                          style={{
                            background: isStopped ? "#f3e8ff" : "#f8fafc",
                            borderRadius: "8px",
                            padding: "10px 12px",
                            fontSize: "12px",
                            color: "#334155",
                            marginBottom: "8px",
                          }}
                        >
                          <div style={{ fontWeight: 600, marginBottom: "4px" }}>
                            Action Execution Details:
                          </div>
                          <div style={{ wordBreak: "break-word", lineHeight: "1.5" }}>
                            {action.notes || "No execution notes recorded."}
                          </div>
                        </div>
                      )}

                      {/* Outcome Details */}
                      {outcome && (
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#6b7280" }}>
                          <span>
                            Amount Recovered:{" "}
                            <strong style={{ color: outcome.amount_recovered > 0 ? "#10b981" : "#6b7280" }}>
                              {formatINR(outcome.amount_recovered)}
                            </strong>
                          </span>
                          <span>Resolved: {new Date(outcome.resolved_at).toLocaleString()}</span>
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
