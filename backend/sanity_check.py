"""
Clean end-to-end sanity script.
Wipes dev.db, seeds 80 events, runs 4 process-batch passes, then
prints the case trail for every event that had a voice_call_hinglish action —
specifically checking for any event that shows multiple RECOVERED outcomes
(which would confirm the double-counting bug).
"""
import os, time, sys, subprocess, threading, json, urllib.request

os.environ["DATABASE_URL"] = "sqlite:///./dev.db"
os.environ["PYTHONPATH"] = "."

# 1 — wipe DB
if os.path.exists("dev.db"):
    os.remove("dev.db")
    print("Deleted dev.db")

# 2 — seed
from app.seed_data import seed
seed(80)

# 3 — start uvicorn in a background thread
import uvicorn, threading

def run_server():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8002, log_level="warning")

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(3)  # let server start

def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:8002{path}") as r:
        return json.loads(r.read())

def post(path):
    req = urllib.request.Request(f"http://127.0.0.1:8002{path}", method="POST", data=b"")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# 4 — 4 batch passes uninterrupted
for i in range(1, 5):
    result = post("/agent/process-batch")
    print(f"Batch pass {i}: {result}")

# 5 — find voice-call events
from app.database import SessionLocal
from app import models

db = SessionLocal()
voice_actions = (
    db.query(models.Action)
    .filter(models.Action.action_type == models.ActionType.VOICE_CALL_HINGLISH)
    .all()
)
event_ids = list({
    db.query(models.Decision).filter(models.Decision.id == a.decision_id).first().event_id
    for a in voice_actions
})
db.close()

print(f"\nFound {len(event_ids)} events with a voice_call_hinglish action.")
print("Checking for double-RECOVERED outcomes...\n")

double_counted = []
for eid in event_ids:
    data = get(f"/dashboard/case/{eid}")
    recovered_outcomes = [o for o in data["outcomes"] if o["status"] == "recovered" and o["amount_recovered"] > 0]
    transcript = data["event"]["demo_transcript"]
    if len(recovered_outcomes) > 1:
        double_counted.append(eid)
        print(f"[DOUBLE-COUNT] event={eid}")
        print(f"  transcript: {transcript}")
        for o in recovered_outcomes:
            print(f"  RECOVERED outcome: amount={o['amount_recovered']}")
    else:
        # Print a summary line for non-doubled events too
        total_recovered = sum(o["amount_recovered"] for o in data["outcomes"])
        statuses = [o["status"] for o in data["outcomes"]]
        print(f"[OK] event={eid[:8]}..  transcript: {transcript[:50]}  | outcomes: {statuses} | total_recovered={total_recovered}")

print(f"\n{'='*60}")
if double_counted:
    print(f"RESULT: DOUBLE-COUNT BUG CONFIRMED on {len(double_counted)} event(s). Proceed with fix.")
else:
    print("RESULT: No double-counting observed on clean run. Bug may have been a DB corruption artifact.")
print("="*60)
