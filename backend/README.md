# AI Revenue Recovery Agent — Backend Skeleton

Detect → diagnose → decide → act → log, for payment failures, checkout
abandonment, subscription failures, and overdue invoices.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set up a local Postgres database, or for fast prototyping switch to SQLite
by setting the `DATABASE_URL` env var:

```bash
export DATABASE_URL="sqlite:///./dev.db"      # quick local dev
# or, for Postgres:
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/revenue_recovery"
```

## Seed sample data

```bash
python -m app.seed_data
```

This creates ~80 synthetic events (failed payments, abandoned checkouts,
failed subscriptions, overdue invoices) so you have something to run the
agent against immediately.

## Run the API

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs (FastAPI's
built-in Swagger UI).

## Demo flow

1. `POST /agent/process-batch` — runs one agent pass over every event
   currently in the system (classifies root cause, picks an action,
   executes it, logs the outcome).
2. Call `POST /agent/process-batch` again a few times — this simulates
   time passing and shows retries escalating (attempt 1 → attempt 2 →
   eventually the stopping rule triggers and `STOPPED` shows up).
3. `GET /dashboard/metrics` — headline numbers: total at risk, total
   recovered, recovery rate %, stopped count, breakdown by channel.
4. `GET /dashboard/case/{event_id}` — full audit trail for one event:
   every decision, action, and outcome in order. This is what proves
   the "compliant escalation + stopping rules + audit trail" bar.

## What's stubbed vs. real

- **Decision engine** (`app/decision_engine.py`) — real logic, not a
  stub. Rule-based on purpose: inspectable, no LLM randomness in the
  core loop. Swap in an LLM classifier only for cases that fall through
  to `UNKNOWN`, if you have time.
- **Executors** (`app/executors.py`) — currently simulated with random
  success rates so the batch demo produces a believable recovered-₹
  number. Replace each function's body with a real SMS/WhatsApp/
  telephony call when you're ready; the interface (return success,
  amount, ref, notes) stays the same.
- **Hinglish voice call** (`execute_voice_call_hinglish`) — this is
  where your fine-tuned Whisper model + a TTS layer plugs in. Build it
  as a standalone service first, test it in isolation, then swap the
  body of this function to call it.

## Next steps (matches your build plan)

- [ ] Wire `execute_voice_call_hinglish` to your Whisper STT + TTS pipeline
- [ ] Build the React dashboard against `/dashboard/metrics` and `/dashboard/case/{id}`
- [ ] Add `promises_to_pay` write path for the invoice/B2B flow
- [ ] Add JWT + RBAC (you've done this twice already — reuse your In Time Tec pattern)
