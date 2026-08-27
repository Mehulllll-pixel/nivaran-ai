import { useEffect, useState, useCallback } from "react";
import { fetchMetrics, fetchEvents, processBatch } from "./api";
import { MetricCards } from "./components/MetricCards";
import { VoiceSpotlight } from "./components/VoiceSpotlight";
import { ChannelChart } from "./components/ChannelChart";
import { EventList } from "./components/EventList";
import { CaseAuditModal } from "./components/CaseAuditModal";
import { RefreshCw, Play, Radio, CheckCircle2, AlertCircle } from "lucide-react";

function App() {
  const [metrics, setMetrics] = useState(null);
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchFeedback, setBatchFeedback] = useState(null);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setError(null);
      const [m, evts] = await Promise.all([fetchMetrics(), fetchEvents()]);
      setMetrics(m);
      setEvents(evts);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRunBatch = async () => {
    try {
      setBatchRunning(true);
      setBatchFeedback(null);
      const res = await processBatch();
      setBatchFeedback(`✓ Batch complete! Processed ${res.events_processed} events.`);
      await loadData();
    } catch (err) {
      setBatchFeedback(`✕ Batch failed: ${err.message}`);
    } finally {
      setBatchRunning(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--bg-main)", color: "var(--text-primary)" }}>
      {/* Top Navigation / Header */}
      <header
        style={{
          background: "linear-gradient(180deg, #10121b 0%, #0c0d15 100%)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          padding: "16px 32px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          position: "sticky",
          top: 0,
          zIndex: 100,
          backdropFilter: "blur(12px)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #6366f1 0%, #4338ca 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#fff",
              fontWeight: 800,
              fontSize: "18px",
              boxShadow: "0 0 16px rgba(99, 102, 241, 0.4)",
            }}
          >
            N
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <h1 style={{ margin: 0, fontSize: "16px", fontWeight: 700, letterSpacing: "-0.02em", color: "#f3f4f6" }}>
                Nivaran AI
              </h1>
              <span
                style={{
                  fontSize: "10px",
                  fontWeight: 700,
                  padding: "1px 6px",
                  borderRadius: "4px",
                  background: "rgba(99, 102, 241, 0.2)",
                  color: "#a5b4fc",
                  border: "1px solid rgba(99, 102, 241, 0.4)",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                <Radio size={10} className="glow-active" color="#818cf8" />
                <span>COMMAND CENTER</span>
              </span>
            </div>
            <p style={{ margin: 0, fontSize: "12px", color: "var(--text-secondary)" }}>
              Autonomous Revenue Recovery & Hinglish Voice Agent
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          {batchFeedback && (
            <span
              style={{
                fontSize: "12px",
                fontWeight: 600,
                color: batchFeedback.startsWith("✓") ? "#34d399" : "#f87171",
                background: batchFeedback.startsWith("✓") ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                padding: "6px 12px",
                borderRadius: "8px",
                border: "1px solid",
                borderColor: batchFeedback.startsWith("✓") ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              {batchFeedback.startsWith("✓") ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
              <span>{batchFeedback}</span>
            </span>
          )}

          <button
            id="run-batch-btn"
            onClick={handleRunBatch}
            disabled={batchRunning}
            style={{
              background: batchRunning
                ? "#2d3042"
                : "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
              color: "#ffffff",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              borderRadius: "8px",
              padding: "9px 16px",
              fontSize: "12px",
              fontWeight: 600,
              cursor: batchRunning ? "not-allowed" : "pointer",
              boxShadow: batchRunning ? "none" : "0 0 16px rgba(99, 102, 241, 0.35)",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.2s ease",
            }}
          >
            {batchRunning ? (
              <>
                <RefreshCw size={13} className="glow-active" style={{ animation: "spin 1s linear infinite" }} />
                <span>Processing Batch (Simulating Time)...</span>
              </>
            ) : (
              <>
                <Play size={13} fill="#ffffff" />
                <span>Run Agent Batch (Simulate Day)</span>
              </>
            )}
          </button>

          <button
            id="refresh-btn"
            onClick={loadData}
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              borderRadius: "8px",
              padding: "9px 12px",
              fontSize: "12px",
              fontWeight: 500,
              color: "#e2e8f0",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255, 255, 255, 0.1)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)")}
          >
            <RefreshCw size={13} />
            <span>Refresh</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main style={{ maxWidth: "1320px", margin: "0 auto", padding: "24px 28px", width: "100%" }}>
        {loading && <p style={{ color: "var(--text-secondary)" }}>Connecting to Nivaran AI telemetry...</p>}
        {error && (
          <div
            style={{
              padding: "16px",
              background: "rgba(239, 68, 68, 0.12)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              borderRadius: "10px",
              color: "#fca5a5",
              marginBottom: "20px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <AlertCircle size={16} />
            <span><strong>Connection Error:</strong> {error}</span>
          </div>
        )}

        {metrics && (
          <>
            {/* KPI Metric Cards */}
            <MetricCards metrics={metrics} />

            {/* Dedicated Voice Recovery Spotlight (Hero Event) */}
            <VoiceSpotlight
              events={events}
              onInspectCase={(id) => setSelectedEventId(id)}
            />

            {/* Revenue Recovery by Channel Chart */}
            <ChannelChart byActionType={metrics.by_action_type} />

            {/* Events Table with Case Audit Trail inspection */}
            <EventList events={events} onSelectEvent={(id) => setSelectedEventId(id)} />
          </>
        )}
      </main>

      {/* Case Audit Trail Modal */}
      {selectedEventId && (
        <CaseAuditModal
          eventId={selectedEventId}
          onClose={() => setSelectedEventId(null)}
        />
      )}
    </div>
  );
}

export default App;
