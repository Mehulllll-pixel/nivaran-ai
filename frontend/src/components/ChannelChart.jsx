import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Mic, BarChart3, Sparkles } from "lucide-react";

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
  voice_call_hinglish: "#6366f1", // Hero primary indigo accent
  sms_nudge: "#3b82f6",
  whatsapp_nudge: "#10b981",
  auto_retry: "#f59e0b",
  invoice_reminder: "#ec4899",
  new_payment_link: "#8b5cf6",
  escalate_human: "#64748b",
};

export function ChannelChart({ byActionType }) {
  if (!byActionType || Object.keys(byActionType).length === 0) {
    return (
      <div
        id="channel-recovery-chart"
        style={{
          background: "#12131c",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "12px",
          padding: "24px",
          marginBottom: "20px",
          textAlign: "center",
          color: "var(--text-muted)",
        }}
      >
        No channel recovery data available yet.
      </div>
    );
  }

  const data = Object.entries(byActionType)
    .map(([key, value]) => ({
      key,
      name: CHANNEL_LABELS[key] || key,
      recovered: value,
      isVoice: key === "voice_call_hinglish",
    }))
    .sort((a, b) => b.recovered - a.recovered);

  const formatINR = (val) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val || 0);
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div
          style={{
            background: "#181a27",
            border: item.isVoice ? "1px solid #6366f1" : "1px solid rgba(255, 255, 255, 0.12)",
            borderRadius: "8px",
            padding: "10px 14px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.6)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
            {item.isVoice && <Sparkles size={12} color="#818cf8" />}
            <span style={{ fontSize: "12px", fontWeight: 600, color: "#f3f4f6" }}>
              {item.name}
            </span>
            {item.isVoice && (
              <span
                style={{
                  fontSize: "10px",
                  background: "rgba(99, 102, 241, 0.2)",
                  color: "#a5b4fc",
                  padding: "1px 6px",
                  borderRadius: "4px",
                  fontWeight: 700,
                }}
              >
                CORE ENGINE
              </span>
            )}
          </div>
          <div style={{ fontSize: "14px", fontWeight: 700, color: item.isVoice ? "#818cf8" : "#34d399" }} className="font-mono">
            {formatINR(item.recovered)}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div
      id="channel-recovery-chart"
      style={{
        background: "linear-gradient(180deg, #131520 0%, #0e1017 100%)",
        border: "1px solid rgba(255, 255, 255, 0.07)",
        borderRadius: "12px",
        padding: "20px 24px",
        marginBottom: "20px",
        boxShadow: "0 4px 20px -2px rgba(0, 0, 0, 0.4), inset 0 1px 0 0 rgba(255, 255, 255, 0.05)",
      }}
    >
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
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <BarChart3 size={17} color="#818cf8" />
            <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 600, color: "#f3f4f6", letterSpacing: "-0.01em" }}>
              Revenue Recovered by Channel
            </h3>
          </div>
          <p style={{ margin: "4px 0 0", fontSize: "12px", color: "var(--text-secondary)" }}>
            Distribution of collected funds across multi-channel automated recovery strategies
          </p>
        </div>

        {/* Highlight badge for Voice Call */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            background: "rgba(99, 102, 241, 0.1)",
            border: "1px solid rgba(99, 102, 241, 0.3)",
            borderRadius: "20px",
            padding: "4px 12px",
            fontSize: "11px",
            color: "#a5b4fc",
          }}
        >
          <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "50%", background: "#6366f1", boxShadow: "0 0 8px #6366f1" }} />
          <span style={{ fontWeight: 600 }}>Voice Call (Hinglish) = Core AI Differentiator</span>
        </div>
      </div>

      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 25 }}>
            <defs>
              {/* Special gradient for voice_call_hinglish */}
              <linearGradient id="voiceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#818cf8" />
                <stop offset="100%" stopColor="#4338ca" />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "#9ca3af", fontFamily: "var(--font-sans)" }}
              interval={0}
              angle={-15}
              textAnchor="end"
              stroke="rgba(255, 255, 255, 0.1)"
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#9ca3af", fontFamily: "var(--font-mono)" }}
              tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
              stroke="rgba(255, 255, 255, 0.1)"
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="recovered" radius={[6, 6, 0, 0]}>
              {data.map((entry) => (
                <Cell
                  key={`cell-${entry.key}`}
                  fill={entry.isVoice ? "url(#voiceGradient)" : CHANNEL_COLORS[entry.key] || "#3b82f6"}
                  stroke={entry.isVoice ? "#a5b4fc" : "none"}
                  strokeWidth={entry.isVoice ? 1 : 0}
                  opacity={entry.isVoice ? 1 : 0.85}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
