"""
verify_hero_demo.py
===================
1. Wipes dev.db and reseeds (80 batch events + 1 hero demo event = 81 total)
2. Finds cust_hero_demo via GET /events
3. Runs process-batch Pass 1 and Pass 2
4. Inspects and prints the complete case audit trail for the hero event
5. Prints the exact event_id for demo notes
"""
import os, time, json, urllib.request, threading

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

# 4. Find hero event
events = get("/events/")
hero = next((e for e in events if e.get("customer_id") == "cust_hero_demo"), None)
if not hero:
    print("ERROR: cust_hero_demo not found in /events!")
    exit(1)

hero_id = hero["id"]
print(f"\nFound Hero Demo Event:")
print(f"  Event ID       : {hero_id}")
print(f"  Customer ID    : {hero['customer_id']}")
print(f"  Amount         : Rs {hero['amount']}")
print(f"  Event Type     : {hero['event_type']}")
print(f"  Reason Code    : {hero['raw_reason_code']}")
print(f"  Demo Transcript: \"{hero['demo_transcript']}\"")

# 5. Run Pass 1
print("\n--- Running Batch Pass 1 (Attempt 1) ---")
res1 = post("/agent/process-batch")
print(f"Pass 1 result: {res1}")

case_p1 = get(f"/dashboard/case/{hero_id}")
print(f"Hero status after Pass 1: Attempt {case_p1['decisions'][-1]['attempt_number']} -> Action: {case_p1['decisions'][-1]['chosen_action']} -> Outcome: {case_p1['outcomes'][-1]['status']}")

# 6. Run Pass 2
print("\n--- Running Batch Pass 2 (Attempt 2: Voice Call) ---")
res2 = post("/agent/process-batch")
print(f"Pass 2 result: {res2}")

# 7. Fetch full case trail
case_p2 = get(f"/dashboard/case/{hero_id}")
print("\n" + "=" * 70)
print(f"HERO EVENT FULL CASE AUDIT TRAIL: {hero_id}")
print("=" * 70)
print(f"Customer   : {case_p2['event']['customer_id']}")
print(f"Amount     : Rs {case_p2['event']['amount']}")
print(f"Transcript : \"{case_p2['event']['demo_transcript']}\"")
print("-" * 70)

for i, decision in enumerate(case_p2["decisions"]):
    action = case_p2["actions"][i] if i < len(case_p2["actions"]) else None
    outcome = case_p2["outcomes"][i] if i < len(case_p2["outcomes"]) else None
    
    print(f"\n[ATTEMPT #{decision['attempt_number']}] Decision: {decision['chosen_action'].upper()} (Root Cause: {decision['root_cause']})")
    print(f"  Reasoning : {decision['reasoning']}")
    if action:
        print(f"  Action    : {action['action_type']} (ref: {action['channel_ref']})")
        print(f"  Notes     : {action['notes']}")
    if outcome:
        print(f"  Outcome   : {outcome['status'].upper()} (Recovered: Rs {outcome['amount_recovered']})")

print("\n" + "=" * 70)
print(f"HERO_EVENT_ID = \"{hero_id}\"")
print("=" * 70)
