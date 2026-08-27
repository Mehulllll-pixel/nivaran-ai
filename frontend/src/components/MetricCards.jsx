import { useEffect, useState, useRef } from "react";
import { AlertCircle, TrendingUp, Percent, ShieldCheck } from "lucide-react";

// Smooth count-up animated value hook
function useCountUp(targetValue, duration = 800) {
  const [displayValue, setDisplayValue] = useState(0);
  const prevValueRef = useRef(0);

  useEffect(() => {
    const startValue = prevValueRef.current;
    const endValue = typeof targetValue === "number" ? targetValue : 0;
    prevValueRef.current = endValue;

    if (startValue === endValue) {
      setDisplayValue(endValue);
      return;
    }

    let startTime = null;
    let animationFrameId;

    const step = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      // easeOutExpo
      const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      const current = startValue + (endValue - startValue) * ease;
      setDisplayValue(current);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(step);
      } else {
        setDisplayValue(endValue);
      }
    };

    animationFrameId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animationFrameId);
  }, [targetValue, duration]);

  return displayValue;
}

function AnimatedINR({ value }) {
  const animated = useCountUp(value || 0);
  return (
    <span className="font-mono">
      {new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
      }).format(animated)}
    </span>
  );
}

function AnimatedPercent({ value }) {
  const animated = useCountUp(value || 0);
  return (
    <span className="font-mono">
      {animated.toFixed(1)}%
    </span>
  );
}

function AnimatedCount({ value }) {
  const animated = useCountUp(value || 0);
  return (
    <span className="font-mono">
      {Math.round(animated)}
    </span>
  );
}

export function MetricCards({ metrics }) {
  if (!metrics) return null;

  const cards = [
    {
      id: "metric-at-risk",
      title: "Total at Risk",
      renderValue: () => <AnimatedINR value={metrics.total_at_risk} />,
      subtext: `${metrics.total_events} initial revenue risk events`,
      icon: AlertCircle,
      accentColor: "var(--status-risk)",
      badgeBg: "rgba(239, 68, 68, 0.12)",
      glowColor: "rgba(239, 68, 68, 0.15)",
    },
    {
      id: "metric-recovered",
      title: "Total Recovered",
      renderValue: () => <AnimatedINR value={metrics.total_recovered} />,
      subtext: "Across automated recovery interventions",
      icon: TrendingUp,
      accentColor: "var(--status-success)",
      badgeBg: "rgba(16, 185, 129, 0.12)",
      glowColor: "rgba(16, 185, 129, 0.15)",
    },
    {
      id: "metric-rate",
      title: "Recovery Efficiency",
      renderValue: () => <AnimatedPercent value={metrics.recovery_rate_pct} />,
      subtext: "Recovered / Total portfolio value",
      icon: Percent,
      accentColor: "var(--accent-primary)",
      badgeBg: "rgba(99, 102, 241, 0.12)",
      glowColor: "rgba(99, 102, 241, 0.18)",
    },
    {
      id: "metric-stopped",
      title: "Compliance Respected",
      renderValue: () => <AnimatedCount value={metrics.stopped_count} />,
      subtext: "Guardrail caps & opt-outs enforced",
      icon: ShieldCheck,
      accentColor: "var(--status-compliance)",
      badgeBg: "rgba(168, 85, 247, 0.12)",
      glowColor: "rgba(168, 85, 247, 0.15)",
    },
  ];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
        gap: "16px",
        marginBottom: "20px",
      }}
    >
      {cards.map((card) => {
        const IconComponent = card.icon;
        return (
          <div
            key={card.id}
            id={card.id}
            style={{
              background: "linear-gradient(180deg, #131520 0%, #0e1017 100%)",
              border: "1px solid rgba(255, 255, 255, 0.07)",
              borderRadius: "12px",
              padding: "20px",
              boxShadow: "0 4px 20px -2px rgba(0, 0, 0, 0.4), inset 0 1px 0 0 rgba(255, 255, 255, 0.05)",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              transition: "transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease",
              position: "relative",
              overflow: "hidden",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.16)";
              e.currentTarget.style.boxShadow = `0 8px 24px -4px rgba(0, 0, 0, 0.6), 0 0 20px -2px ${card.glowColor}`;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.07)";
              e.currentTarget.style.boxShadow = "0 4px 20px -2px rgba(0, 0, 0, 0.4), inset 0 1px 0 0 rgba(255, 255, 255, 0.05)";
            }}
          >
            {/* Top row: Title and Icon */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  color: "var(--text-secondary)",
                }}
              >
                {card.title}
              </span>
              <div
                style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "8px",
                  background: card.badgeBg,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: card.accentColor,
                  border: `1px solid ${card.accentColor}33`,
                }}
              >
                <IconComponent size={17} strokeWidth={2.2} />
              </div>
            </div>

            {/* Value */}
            <div
              style={{
                fontSize: "28px",
                fontWeight: 700,
                color: card.accentColor,
                lineHeight: "1.2",
                marginBottom: "6px",
              }}
            >
              {card.renderValue()}
            </div>

            {/* Subtext */}
            <div
              style={{
                fontSize: "12px",
                color: "var(--text-muted)",
              }}
            >
              {card.subtext}
            </div>
          </div>
        );
      })}
    </div>
  );
}
