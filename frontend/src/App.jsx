import { useEffect, useState, useCallback } from "react";
import { fetchMetrics, fetchEvents, processBatch } from "./api";
import { MetricCards } from "./components/MetricCards";
import { ChannelChart } from "./components/ChannelChart";
import { EventList } from "./components/EventList";
import { CaseAuditModal } from "./components/CaseAuditModal";

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
    <div style={{ minHeight: "100vh", backgroundColor: "#f3f4f6", color: "#111827", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" }}>
      {/* Top Navigation / Header */}
      <header
        style={{
          background: "#ffffff",
          borderBottom: "1px solid #e5e7eb",
          padding: "16px 32px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#fff",
              fontWeight: 800,
              fontSize: "18px",
            }}
          >
            N
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: "18px", fontWeight: 700, letterSpacing: "-0.02em" }}>
              Nivaran AI
            </h1>
            <p style={{ margin: 0, fontSize: "12px", color: "#6b7280" }}>
              Autonomous Revenue Recovery & Hinglish Voice Agent
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {batchFeedback && (
            <span
              style={{
                fontSize: "12px",
                fontWeight: 600,
                color: batchFeedback.startsWith("✓") ? "#059669" : "#dc2626",
                background: batchFeedback.startsWith("✓") ? "#ecfdf5" : "#fef2f2",
                padding: "6px 12px",
                borderRadius: "8px",
                border: "1px solid",
                borderColor: batchFeedback.startsWith("✓") ? "#a7f3d0" : "#fecaca",
              }}
            >
              {batchFeedback}
            </span>
          )}

          <button
            id="run-batch-btn"
            onClick={handleRunBatch}
            disabled={batchRunning}
            style={{
              background: batchRunning ? "#9ca3af" : "linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)",
              color: "#ffffff",
              border: "none",
              borderRadius: "8px",
              padding: "10px 18px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: batchRunning ? "not-allowed" : "pointer",
              boxShadow: "0 2px 4px rgba(79, 70, 229, 0.2)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            {batchRunning ? "Processing Batch (Simulating Time)..." : "▶ Run Agent Batch (Simulate Day)"}
          </button>

          <button
            id="refresh-btn"
            onClick={loadData}
            style={{
              background: "#f9fafb",
              border: "1px solid #d1d5db",
              borderRadius: "8px",
              padding: "9px 14px",
              fontSize: "13px",
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            ↻ Refresh
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main style={{ maxWidth: "1280px", margin: "0 auto", padding: "28px 24px" }}>
        {loading && <p style={{ color: "#6b7280" }}>Connecting to Nivaran AI backend...</p>}
        {error && (
          <div style={{ padding: "16px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "10px", color: "#b91c1c", marginBottom: "20px" }}>
            <strong>Connection Error:</strong> {error}
          </div>
        )}

        {metrics && (
          <>
            {/* Phase 2: KPI Metric Cards */}
            <MetricCards metrics={metrics} />

            {/* Phase 2: Revenue Recovery by Channel Chart */}
            <ChannelChart byActionType={metrics.by_action_type} />

            {/* Phase 3: Events Table with Case Audit Trail inspection */}
            <EventList events={events} onSelectEvent={(id) => setSelectedEventId(id)} />
          </>
        )}
      </main>

      {/* Phase 3: Case Audit Trail Modal */}
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
