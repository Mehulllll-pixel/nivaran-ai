"""
run_reweighted_experiment.py
============================
1. Wipes dev.db
2. Reseeds 80 events with the new weighted seed distribution
3. Runs 6 process-batch passes to verify stabilization
4. Analyzes root cause distribution, final state counts, voice_call_hinglish metrics, and by_action_type revenue
"""
import os, time, json, urllib.request, threading
from collections import Counter

os.environ["DATABASE_URL"] = "sqlite:///./dev.db"
os.environ["PYTHONPATH"] = "."
os.environ["PYTHONIOENCODING"] = "utf-8"

# 1. Wipe dev.db
if os.path.exists("dev.db"):
    os.remove("dev.db")
    print("Deleted old dev.db")

# 2. Reseed
from app.seed_data import seed
seed(80)

# Analyze initial root causes
from app.database import SessionLocal
from app import models
from app.decision_engine import classify_root_cause

db = SessionLocal()
events = db.query(models.Event).all()
initial_rcs = Counter(classify_root_cause(e.event_type, e.raw_reason_code).value for e in events)
db.close()

print("\n--- Initial Seeded Root Cause Distribution (80 Events) ---")
target_causes = {"insufficient_funds", "user_abandoned", "invoice_unpaid"}
target_count = 0
for rc, cnt in initial_rcs.most_common():
    is_target = " (VOICE ELIGIBLE)" if rc in target_causes else ""
    if rc in target_causes:
        target_count += cnt
    print(f"  {rc:<22}: {cnt:>2} ({cnt/80*100:>5.1f}%){is_target}")
print(f"Total Voice-Eligible Root Causes: {target_count}/80 ({target_count/80*100:.1f}%)")

# 3. Start server
import uvicorn
def start_server():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="warning")

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()
time.sleep(3)

def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:8000{path}") as r:
        return json.loads(r.read())

def post(path):
    req = urllib.request.Request(f"http://127.0.0.1:8000{path}", method="POST", data=b"")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

passes_data = []
for p in range(1, 7):
    res = post("/agent/process-batch")
    m = get("/dashboard/metrics")
    passes_data.append((p, m['stopped_count'], m['total_recovered'], m['recovery_rate_pct']))
    print(f"Pass {p}: Processed={res['events_processed']}, Stopped={m['stopped_count']}, Recovered=Rs {m['total_recovered']:.2f}, Rate={m['recovery_rate_pct']}%")

print("\n" + "=" * 65)
print("BATCH STABILIZATION SUMMARY TABLE:")
print("=" * 65)
print(f"{'Pass #':<8} | {'Stopped Count':<15} | {'Total Recovered (Rs)':<22} | {'Recovery Rate %':<15}")
print("-" * 65)
for p, s, r, rate in passes_data:
    print(f"{p:<8} | {s:<15} | {r:<22} | {rate:<15}")

# 4. Final State & Voice Call Analysis
db = SessionLocal()
events = db.query(models.Event).all()

recovered_events = []
stopped_events = []
pending_events = []

voice_attempted_events = []
voice_recovered_events = []

for e in events:
    decisions = db.query(models.Decision).filter(models.Decision.event_id == e.id).order_by(models.Decision.attempt_number).all()
    d_ids = [d.id for d in decisions]
    actions = db.query(models.Action).filter(models.Action.decision_id.in_(d_ids)).all()
    action_map = {a.id: a for a in actions}
    outcomes = db.query(models.Outcome).filter(models.Outcome.action_id.in_([a.id for a in actions])).all()
    
    statuses = [o.status.value for o in outcomes]
    action_types = [a.action_type.value for a in actions]
    
    if "voice_call_hinglish" in action_types:
        voice_attempted_events.append(e)
    
    if "recovered" in statuses:
        recovered_events.append(e)
        # Check if the recovered action was voice call
        for o in outcomes:
            if o.status.value == "recovered" and o.amount_recovered > 0:
                act = action_map.get(o.action_id)
                if act and act.action_type.value == "voice_call_hinglish":
                    voice_recovered_events.append((e, o.amount_recovered, act.notes))
    elif "stopped" in statuses:
        stopped_events.append(e)
    elif "pending" in statuses:
        pending_events.append(e)

final_metrics = get("/dashboard/metrics")

print("\n" + "=" * 65)
print("FINAL BREAKDOWN & VOICE RECOVERY METRICS:")
print("=" * 65)
print(f"Total Events             : {len(events)}")
print(f"  - RECOVERED            : {len(recovered_events)}")
print(f"  - STOPPED              : {len(stopped_events)}")
print(f"  - PENDING              : {len(pending_events)}")
print(f"\nVoice Call (Hinglish) Statistics:")
print(f"  - Events with Voice Call Attempt : {len(voice_attempted_events)}")
print(f"  - Events Recovered via Voice Call: {len(voice_recovered_events)}")
print(f"  - Voice Call Recovered Amount    : Rs {final_metrics['by_action_type'].get('voice_call_hinglish', 0.0):,.2f}")

print("\nBy-Action-Type Recovery Breakdown:")
for channel, amt in sorted(final_metrics['by_action_type'].items(), key=lambda x: x[1], reverse=True):
    print(f"  {channel:<22}: Rs {amt:>12,.2f}")

print("=" * 65)

db.close()
