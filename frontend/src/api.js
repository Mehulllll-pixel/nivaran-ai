const API_BASE = "http://127.0.0.1:8000";

export async function fetchMetrics() {
  const res = await fetch(`${API_BASE}/dashboard/metrics`);
  if (!res.ok) {
    throw new Error(`Failed to fetch metrics: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchEvents() {
  const res = await fetch(`${API_BASE}/events/`);
  if (!res.ok) {
    throw new Error(`Failed to fetch events: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchCaseTimeline(eventId) {
  const res = await fetch(`${API_BASE}/dashboard/case/${eventId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch case: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function processBatch() {
  const res = await fetch(`${API_BASE}/agent/process-batch`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Failed to process batch: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fulfillPromise(promiseId) {
  const res = await fetch(`${API_BASE}/agent/fulfill-promise/${promiseId}`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Failed to fulfill promise: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
