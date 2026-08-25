export function MetricCards({ metrics }) {
  if (!metrics) return null;

  const formatINR = (val) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(val || 0);
  };

  const cards = [
    {
      id: "metric-at-risk",
      title: "Total at Risk",
      value: formatINR(metrics.total_at_risk),
      subtext: `${metrics.total_events} total events`,
      color: "#ef4444",
      bg: "rgba(239, 68, 68, 0.08)",
    },
    {
      id: "metric-recovered",
      title: "Total Recovered",
      value: formatINR(metrics.total_recovered),
      subtext: "Across all recovery channels",
      color: "#10b981",
      bg: "rgba(16, 185, 129, 0.08)",
    },
    {
      id: "metric-rate",
      title: "Recovery Rate",
      value: `${metrics.recovery_rate_pct}%`,
      subtext: "Recovered / Total at risk",
      color: "#3b82f6",
      bg: "rgba(59, 130, 246, 0.08)",
    },
    {
      id: "metric-stopped",
      title: "Stopped (Compliance Cap)",
      value: metrics.stopped_count,
      subtext: "Max attempts reached / Opt-outs",
      color: "#8b5cf6",
      bg: "rgba(139, 92, 246, 0.08)",
    },
  ];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "16px",
        marginBottom: "24px",
      }}
    >
      {cards.map((card) => (
        <div
          key={card.id}
          id={card.id}
          style={{
            background: "#ffffff",
            border: "1px solid #e5e7eb",
            borderRadius: "12px",
            padding: "20px",
            boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          }}
        >
          <div style={{ fontSize: "13px", color: "#6b7280", fontWeight: 500, marginBottom: "8px" }}>
            {card.title}
          </div>
          <div style={{ fontSize: "26px", fontWeight: 700, color: card.color, marginBottom: "6px" }}>
            {card.value}
          </div>
          <div style={{ fontSize: "12px", color: "#9ca3af" }}>
            {card.subtext}
          </div>
        </div>
      ))}
    </div>
  );
}
