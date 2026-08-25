import { useState } from "react";

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
    const matchesSearch =
      (e.customer_id || "").toLowerCase().includes(search.toLowerCase()) ||
      (e.demo_transcript || "").toLowerCase().includes(search.toLowerCase()) ||
      (e.id || "").toLowerCase().includes(search.toLowerCase());
    const matchesFilter =
      filterType === "all" || e.event_type === filterType;
    return matchesSearch && matchesFilter;
  });

  return (
    <div
      id="events-table-card"
      style={{
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: "12px",
        padding: "20px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
      }}
    >
      {/* Header with Search and Filter */}
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
        <div>
          <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 600, color: "#111827" }}>
            Revenue Risk Events ({filteredEvents.length})
          </h3>
          <p style={{ margin: "4px 0 0", fontSize: "13px", color: "#6b7280" }}>
            Click any row to inspect the decision engine audit trail and voice call transcript
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <input
            id="event-search-input"
            type="text"
            placeholder="Search customer, transcript..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              padding: "8px 12px",
              borderRadius: "8px",
              border: "1px solid #d1d5db",
              fontSize: "13px",
              outline: "none",
              minWidth: "220px",
            }}
          />
          <select
            id="event-type-filter"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{
              padding: "8px 12px",
              borderRadius: "8px",
              border: "1px solid #d1d5db",
              fontSize: "13px",
              background: "#fff",
              cursor: "pointer",
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
            borderCollapse: "collapse",
            fontSize: "13px",
            textAlign: "left",
          }}
        >
          <thead>
            <tr style={{ background: "#f9fafb", borderBottom: "1px solid #e5e7eb", color: "#4b5563" }}>
              <th style={{ padding: "12px 14px", fontWeight: 600 }}>Customer ID</th>
              <th style={{ padding: "12px 14px", fontWeight: 600 }}>Event Type</th>
              <th style={{ padding: "12px 14px", fontWeight: 600 }}>Reason Code</th>
              <th style={{ padding: "12px 14px", fontWeight: 600, textAlign: "right" }}>Amount</th>
              <th style={{ padding: "12px 14px", fontWeight: 600 }}>Demo Hinglish Transcript</th>
              <th style={{ padding: "12px 14px", fontWeight: 600, textAlign: "center" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ padding: "24px", textAlign: "center", color: "#9ca3af" }}>
                  No events found matching your filter.
                </td>
              </tr>
            ) : (
              filteredEvents.map((evt) => (
                <tr
                  key={evt.id}
                  onClick={() => onSelectEvent(evt.id)}
                  style={{
                    borderBottom: "1px solid #f3f4f6",
                    cursor: "pointer",
                    transition: "background 0.15s ease",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#f8fafc")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <td style={{ padding: "12px 14px", fontWeight: 600, color: "#1e293b", fontFamily: "monospace" }}>
                    {evt.customer_id}
                  </td>
                  <td style={{ padding: "12px 14px" }}>
                    <span
                      style={{
                        padding: "3px 8px",
                        borderRadius: "6px",
                        fontSize: "11px",
                        fontWeight: 600,
                        background: "#e0f2fe",
                        color: "#0369a1",
                      }}
                    >
                      {evt.event_type}
                    </span>
                  </td>
                  <td style={{ padding: "12px 14px", color: "#64748b" }}>
                    {evt.raw_reason_code || "—"}
                  </td>
                  <td style={{ padding: "12px 14px", textAlign: "right", fontWeight: 600, color: "#111827" }}>
                    {formatINR(evt.amount)}
                  </td>
                  <td
                    style={{
                      padding: "12px 14px",
                      maxWidth: "280px",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      color: "#475569",
                      fontStyle: "italic",
                    }}
                    title={evt.demo_transcript || ""}
                  >
                    {evt.demo_transcript ? `"${evt.demo_transcript}"` : "—"}
                  </td>
                  <td style={{ padding: "12px 14px", textAlign: "center" }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectEvent(evt.id);
                      }}
                      style={{
                        background: "#eff6ff",
                        border: "1px solid #bfdbfe",
                        color: "#1d4ed8",
                        borderRadius: "6px",
                        padding: "4px 10px",
                        fontSize: "12px",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
