import { useState } from "react";
import { Search, Filter, Layers, ArrowUpRight } from "lucide-react";

export function EventList({ events, onSelectEvent }) {
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("all");

  const formatINR = (val) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(val || 0);
  };

  const filteredEvents = (events || []).filter((e) => {
    const transcript = e.voice_transcript || e.demo_transcript || "";
    const matchesSearch =
      (e.customer_id || "").toLowerCase().includes(search.toLowerCase()) ||
      transcript.toLowerCase().includes(search.toLowerCase()) ||
      (e.id || "").toLowerCase().includes(search.toLowerCase());
    const matchesFilter =
      filterType === "all" || e.event_type === filterType;
    return matchesSearch && matchesFilter;
  });

  const getEventTypeBadge = (type) => {
    switch (type) {
      case "payment_failed":
        return { bg: "rgba(239, 68, 68, 0.12)", color: "#f87171", border: "rgba(239, 68, 68, 0.3)" };
      case "subscription_failed":
        return { bg: "rgba(245, 158, 11, 0.12)", color: "#fbbf24", border: "rgba(245, 158, 11, 0.3)" };
      case "checkout_abandoned":
        return { bg: "rgba(168, 85, 247, 0.12)", color: "#c084fc", border: "rgba(168, 85, 247, 0.3)" };
      case "invoice_overdue":
        return { bg: "rgba(59, 130, 246, 0.12)", color: "#60a5fa", border: "rgba(59, 130, 246, 0.3)" };
      default:
        return { bg: "rgba(255, 255, 255, 0.08)", color: "#9ca3af", border: "rgba(255, 255, 255, 0.12)" };
    }
  };

  return (
    <div
      id="events-table-card"
      style={{
        background: "linear-gradient(180deg, #131520 0%, #0e1017 100%)",
        border: "1px solid rgba(255, 255, 255, 0.07)",
        borderRadius: "12px",
        padding: "20px 24px",
        boxShadow: "0 4px 20px -2px rgba(0, 0, 0, 0.4), inset 0 1px 0 0 rgba(255, 255, 255, 0.05)",
      }}
    >
      {/* Header with Search and Filter */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "14px",
          marginBottom: "18px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Layers size={17} color="#818cf8" />
            <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 600, color: "#f3f4f6", letterSpacing: "-0.01em" }}>
              Revenue Risk Events <span className="font-mono" style={{ color: "var(--text-muted)", fontSize: "13px" }}>({filteredEvents.length})</span>
            </h3>
          </div>
          <p style={{ margin: "4px 0 0", fontSize: "12px", color: "var(--text-secondary)" }}>
            Select any case to inspect decision tree rules, reasoning, and voice conversation audit logs
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          {/* Search box */}
          <div style={{ position: "relative" }}>
            <Search
              size={14}
              style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "#6b7280" }}
            />
            <input
              id="event-search-input"
              type="text"
              placeholder="Search customer, transcript..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                padding: "8px 12px 8px 32px",
                borderRadius: "8px",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                background: "#0c0d14",
                color: "#f3f4f6",
                fontSize: "12px",
                outline: "none",
                minWidth: "220px",
                transition: "border-color 0.2s ease, box-shadow 0.2s ease",
              }}
              onFocus={(e) => {
                e.target.style.borderColor = "var(--accent-primary)";
                e.target.style.boxShadow = "0 0 0 2px rgba(99, 102, 241, 0.2)";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "rgba(255, 255, 255, 0.12)";
                e.target.style.boxShadow = "none";
              }}
            />
          </div>

          {/* Filter dropdown */}
          <select
            id="event-type-filter"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{
              padding: "8px 12px",
              borderRadius: "8px",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              background: "#0c0d14",
              color: "#f3f4f6",
              fontSize: "12px",
              cursor: "pointer",
              outline: "none",
            }}
          >
            <option value="all">All Event Types</option>
            <option value="payment_failed">Payment Failed</option>
            <option value="subscription_failed">Subscription Failed</option>
            <option value="checkout_abandoned">Checkout Abandoned</option>
            <option value="invoice_overdue">Invoice Overdue</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: "auto" }}>
        <table
          id="events-table"
          style={{
            width: "100%",
            borderCollapse: "separate",
            borderSpacing: "0",
            fontSize: "13px",
            textAlign: "left",
          }}
        >
          <thead>
            <tr style={{ background: "#0c0d14", color: "#9ca3af", borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}>
              <th style={{ padding: "10px 14px", fontWeight: 600, fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.04em" }}>Customer ID</th>
              <th style={{ padding: "10px 14px", fontWeight: 600, fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.04em" }}>Event Type</th>
              <th style={{ padding: "10px 14px", fontWeight: 600, fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.04em" }}>Reason Code</th>
              <th style={{ padding: "10px 14px", fontWeight: 600, fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.04em", textAlign: "right" }}>Amount</th>
              <th style={{ padding: "10px 14px", fontWeight: 600, fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.04em" }}>Hinglish Spoken Transcript</th>
              <th style={{ padding: "10px 14px", fontWeight: 600, fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.04em", textAlign: "center" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
                  No events found matching your search filter.
                </td>
              </tr>
            ) : (
              filteredEvents.map((evt) => {
                const badge = getEventTypeBadge(evt.event_type);
                const isHero = evt.customer_id === "cust_hero_demo";

                return (
                  <tr
                    key={evt.id}
                    onClick={() => onSelectEvent(evt.id)}
                    style={{
                      borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                      cursor: "pointer",
                      transition: "background 0.2s ease, transform 0.2s ease",
                      background: isHero ? "rgba(99, 102, 241, 0.05)" : "transparent",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = isHero
                        ? "rgba(99, 102, 241, 0.12)"
                        : "rgba(255, 255, 255, 0.03)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = isHero
                        ? "rgba(99, 102, 241, 0.05)"
                        : "transparent";
                    }}
                  >
                    <td style={{ padding: "12px 14px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span
                          className="font-mono"
                          style={{
                            fontWeight: 600,
                            color: isHero ? "#a5b4fc" : "#e2e8f0",
                            fontSize: "12px",
                          }}
                        >
                          {evt.customer_id}
                        </span>
                        {isHero && (
                          <span
                            style={{
                              fontSize: "9px",
                              fontWeight: 700,
                              background: "rgba(99, 102, 241, 0.25)",
                              color: "#c7d2fe",
                              padding: "1px 5px",
                              borderRadius: "4px",
                              border: "1px solid rgba(99, 102, 241, 0.4)",
                            }}
                          >
                            HERO
                          </span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <span
                        style={{
                          padding: "3px 8px",
                          borderRadius: "6px",
                          fontSize: "11px",
                          fontWeight: 600,
                          background: badge.bg,
                          color: badge.color,
                          border: `1px solid ${badge.border}`,
                        }}
                      >
                        {evt.event_type}
                      </span>
                    </td>
                    <td style={{ padding: "12px 14px", color: "var(--text-secondary)", fontSize: "12px" }}>
                      {evt.raw_reason_code || "—"}
                    </td>
                    <td
                      className="font-mono"
                      style={{
                        padding: "12px 14px",
                        textAlign: "right",
                        fontWeight: 600,
                        color: "#f3f4f6",
                      }}
                    >
                      {formatINR(evt.amount)}
                    </td>
                    <td
                      style={{
                        padding: "12px 14px",
                        maxWidth: "280px",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        color: evt.voice_transcript ? "#94a3b8" : "#4b5563",
                        fontStyle: "italic",
                        fontSize: "12px",
                      }}
                      title={evt.voice_transcript || ""}
                    >
                      {evt.voice_transcript ? `"${evt.voice_transcript}"` : "—"}
                    </td>
                    <td style={{ padding: "12px 14px", textAlign: "center" }}>
                      <button
                        id={`inspect-btn-${evt.customer_id}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectEvent(evt.id);
                        }}
                        style={{
                          background: isHero ? "rgba(99, 102, 241, 0.2)" : "rgba(255, 255, 255, 0.05)",
                          border: isHero ? "1px solid rgba(99, 102, 241, 0.4)" : "1px solid rgba(255, 255, 255, 0.12)",
                          color: isHero ? "#c7d2fe" : "#e2e8f0",
                          borderRadius: "6px",
                          padding: "4px 10px",
                          fontSize: "11px",
                          fontWeight: 600,
                          cursor: "pointer",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          transition: "all 0.2s ease",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = "rgba(99, 102, 241, 0.35)";
                          e.currentTarget.style.borderColor = "#6366f1";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = isHero ? "rgba(99, 102, 241, 0.2)" : "rgba(255, 255, 255, 0.05)";
                          e.currentTarget.style.borderColor = isHero ? "rgba(99, 102, 241, 0.4)" : "rgba(255, 255, 255, 0.12)";
                        }}
                      >
                        <span>Inspect</span>
                        <ArrowUpRight size={11} />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
