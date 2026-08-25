import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const CHANNEL_LABELS = {
  voice_call_hinglish: "Voice Call (Hinglish)",
  sms_nudge: "SMS Nudge",
  whatsapp_nudge: "WhatsApp Nudge",
  auto_retry: "Auto Retry",
  invoice_reminder: "Invoice Reminder",
  new_payment_link: "New Payment Link",
  escalate_human: "Human Escalation",
  stopped: "Stopped",
};

const CHANNEL_COLORS = {
  voice_call_hinglish: "#6366f1",
  sms_nudge: "#3b82f6",
  whatsapp_nudge: "#10b981",
  auto_retry: "#f59e0b",
  invoice_reminder: "#ec4899",
  new_payment_link: "#8b5cf6",
};

export function ChannelChart({ byActionType }) {
  if (!byActionType || Object.keys(byActionType).length === 0) {
    return (
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: "12px",
          padding: "24px",
          marginBottom: "24px",
          textAlign: "center",
          color: "#9ca3af",
        }}
      >
        No channel recovery data available yet.
      </div>
    );
  }

  const data = Object.entries(byActionType).map(([key, value]) => ({
    key,
    name: CHANNEL_LABELS[key] || key,
    recovered: value,
  })).sort((a, b) => b.recovered - a.recovered);

  const formatINR = (val) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val || 0);
  };

  return (
    <div
      id="channel-recovery-chart"
      style={{
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: "12px",
        padding: "20px",
        marginBottom: "24px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
      }}
    >
      <div style={{ marginBottom: "16px" }}>
        <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 600, color: "#111827" }}>
          Revenue Recovered by Channel
        </h3>
        <p style={{ margin: "4px 0 0", fontSize: "13px", color: "#6b7280" }}>
          Breakdown of total ₹ collected across automated recovery interventions
        </p>
      </div>

      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 20, left: 20, bottom: 25 }}>
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "#4b5563" }}
              interval={0}
              angle={-15}
              textAnchor="end"
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#4b5563" }}
              tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip
              formatter={(value) => [formatINR(value), "Recovered"]}
              contentStyle={{
                backgroundColor: "#1f2937",
                borderRadius: "8px",
                color: "#fff",
                border: "none",
                fontSize: "12px",
              }}
            />
            <Bar dataKey="recovered" radius={[6, 6, 0, 0]}>
              {data.map((entry) => (
                <Cell
                  key={`cell-${entry.key}`}
                  fill={CHANNEL_COLORS[entry.key] || "#3b82f6"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
